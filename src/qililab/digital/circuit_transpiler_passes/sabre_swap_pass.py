# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import math
import random
from collections import deque
from typing import Iterable

from qilisdk.digital import (
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U3,
    Circuit,
    Gate,
    M,
)
from rustworkx import PyGraph

from .circuit_transpiler_pass import CircuitTranspilerPass


class SabreSwapPass(CircuitTranspilerPass):
    """
    SABRE routing (SWAP insertion) for 1Q/2Q circuits on an undirected coupling graph.

    Inputs
    ------
    coupling : rustworkx.PyGraph
        Undirected device graph. Node indices are physical qubits (labels need not be contiguous).
    initial_layout : list[int] | None
        Logical -> physical mapping to start from (e.g., from SabreLayoutPass.last_layout).
        If None, uses the lowest-indexed physical qubits provided by the coupling graph.

    Heuristic (SABRE-style)
    -----------------------
    When a 2Q gate's mapped endpoints are non-adjacent, choose one SWAP on an edge
    touching the mapped endpoints of the current front-set gates that minimizes:

        cost = sum_{g in F} dist(p_u, p_v) * (1 + decay[p_u] + decay[p_v])
             + beta * sum_{g in E} dist(p_u, p_v)

    where F is the per-qubit first unscheduled 2Q gate and E is a small look-ahead set.
    A light decay penalty discourages thrashing.

    Behavior
    --------
    - Returns a **new** Circuit with 1Q gates mapped and SWAPs inserted before each
      non-adjacent 2Q gate so that every emitted 2Q gate acts on an edge of `coupling`.
    - Preserves the original **gate order** (no reordering/commutation across the list).

    Notes
    -----
    - Supports 1Q and 2Q gates (CNOT, CZ, SWAP, generic Controlled with one control).
      Multi-qubit (>2) non-SWAP gates should be decomposed before routing.
    """

    def __init__(
        self,
        coupling: PyGraph,
        *,
        initial_layout: list[int] | None = None,
        seed: int | None = None,
        lookahead_size: int = 10,
        beta: float = 0.8,
        decay_delta: float = 0.001,
        decay_lambda: float = 0.99,
        max_swaps_factor: float = 64.0,
        max_attempts: int = 10,
    ) -> None:
        """Configure SABRE swap routing behavior.

        Args:
            coupling (PyGraph): Undirected coupling graph describing allowed physical qubit
                connections that two-qubit gates must follow.
            initial_layout (list[int] | None): Optional logical-to-physical assignment used to
                seed the routing; defaults to an identity-style mapping if omitted.
            seed (int | None): Base seed for the stochastic swap scoring and for retries when
                the heuristic restarts.
            lookahead_size (int): Number of future two-qubit gates considered in SABRE's
                extended set when scoring candidate swaps.
            beta (float): Weight balancing the extended-set cost versus the immediate front-set
                cost in the SABRE objective.
            decay_delta (float): Increment applied to decay penalties after each physical swap to
                discourage immediate reuse of the same qubits.
            decay_lambda (float): Multiplicative decay factor applied per iteration so older swap
                penalties gradually fade.
            max_swaps_factor (float): Multiplier that converts the current distance between gate
                qubits into the per-gate swap budget before treating the attempt as failed.
            max_attempts (int): Maximum number of independent SABRE attempts (with varied seeds)
                to run before propagating a swap-budget failure.
        """
        if not isinstance(coupling, PyGraph):
            raise TypeError("SabreSwapPass requires a rustworkx.PyGraph (undirected).")
        self.coupling = coupling
        self.initial_layout = initial_layout
        self.seed = seed
        self.lookahead_size = int(lookahead_size)
        self.beta = float(beta)
        self.decay_delta = float(decay_delta)
        self.decay_lambda = float(decay_lambda)
        self.max_swaps_factor = float(max_swaps_factor)
        self.max_attempts = int(max_attempts)

        # Diagnostics
        self.last_swap_count: int | None = None
        self.last_final_layout: list[int] | None = None

    # ----------------------- public API -----------------------

    def run(self, circuit: Circuit) -> Circuit:
        attempts = max(1, self.max_attempts)
        last_exc: RuntimeError | None = None
        base_seed = self.seed
        # Obtain layout hint without mutating instance attributes so repeated runs
        # do not accidentally persist stale mappings.
        layout_hint: list[int] | None = None
        if self.initial_layout is not None:
            layout_hint = list(self.initial_layout)
        elif self.context is not None and self.context.initial_layout:
            layout_hint = list(self.context.initial_layout)

        for attempt in range(attempts):
            attempt_seed = None if base_seed is None else base_seed + attempt
            try:
                out, swap_count, final_layout = self._run_once(
                    circuit,
                    attempt_seed,
                    layout_hint,
                )
            except RuntimeError as exc:
                if "Exceeded swap budget" not in str(exc):
                    raise
                last_exc = exc
                continue

            self.last_swap_count = swap_count
            self.last_final_layout = final_layout

            if self.context is not None:
                self.context.final_layout = list(self.last_final_layout or [])
                self.context.metrics["swap_count"] = self.last_swap_count

            self.append_circuit_to_context(out)
            return out

        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"SABRE routing failed after {attempts} attempts.")

    def _run_once(
        self,
        circuit: Circuit,
        seed: int | None,
        layout_hint: list[int] | None,
    ) -> tuple[Circuit, int, list[int]]:
        rng = random.Random(seed)  # noqa: S311

        n_logical = circuit.nqubits
        phys_nodes = sorted(int(x) for x in self.coupling.node_indices())
        if not phys_nodes:
            raise ValueError("Coupling graph has no nodes.")
        num_phys_nodes = len(phys_nodes)
        phys_index = {node: idx for idx, node in enumerate(phys_nodes)}
        max_phys_label_plus_one = max(phys_nodes) + 1

        active_qubits = {int(q) for g in circuit.gates for q in g.qubits}
        layout = self._init_layout(n_logical, phys_nodes, active_qubits, layout_hint)
        inv_layout = self._invert_layout(layout, phys_index)
        dist = self._apsp_unweighted(self.coupling, phys_nodes, phys_index)

        # Preprocess 2Q structure for SABRE scoring
        twoq_ops_idx, twoq_pairs, per_qubit = self._twoq_structure(circuit)
        m = len(twoq_pairs)
        scheduled = [False] * m
        pos = [0] * n_logical

        def advance_front_for(q: int) -> None:
            L = per_qubit[q]
            i = pos[q]
            while i < len(L) and scheduled[L[i]]:
                i += 1
            pos[q] = i

        for q in range(n_logical):
            advance_front_for(q)

        # Output circuit will use physical indices; ensure capacity for max physical index we may touch.
        out_n = max(
            max_phys_label_plus_one,
            max(layout) + 1 if layout else max_phys_label_plus_one,
            circuit.nqubits,
        )
        out = Circuit(out_n)

        # Decay penalties on physical qubits
        decay = [0.0] * num_phys_nodes
        swap_count = 0

        # Map from op index -> local 2Q index
        op_to_2q = {op_i: k for k, op_i in enumerate(twoq_ops_idx)}

        # --- main sweep over original gates, preserving order ---
        for op_idx, g in enumerate(circuit.gates):
            qs = g.qubits

            # 1Q (or measurement / any non-2Q) -> just map and emit
            if len(qs) <= 1 or isinstance(g, M):
                mapped = tuple(layout[q] for q in qs)
                out.add(self._retarget_gate(g, mapped))
                continue

            # We currently support only 2Q routing (SWAP, CNOT, CZ, single-control Controlled)
            if len(qs) != 2:
                raise NotImplementedError(
                    f"Routing of {type(g).__name__} with arity {len(qs)} not supported. "
                    "Please decompose to 1Q/2Q gates before routing."
                )

            u, v = qs
            k = op_to_2q[op_idx]  # local 2Q index for SABRE bookkeeping

            # While mapped endpoints are not adjacent, insert a SABRE-chosen SWAP
            dist_uv = dist[phys_index[layout[u]]][phys_index[layout[v]]]
            max_swaps_this_gate = int(self.max_swaps_factor * max(1, dist_uv))
            steps = 0
            while dist[phys_index[layout[u]]][phys_index[layout[v]]] != 1:
                steps += 1
                if steps > max_swaps_this_gate:
                    raise RuntimeError(
                        f"Exceeded swap budget while routing gate {type(g).__name__}{qs}: "
                        "graph may be disconnected or heuristic stuck."
                    )

                # Front set F: first unscheduled 2Q gate per logical qubit
                F = self._front_set(per_qubit, pos, scheduled)
                # Ensure current gate is in F (it usually is, but be robust)
                F.add(k)
                # Extended set E
                E = self._extended_set(per_qubit, pos, self.lookahead_size)

                # Build candidate physical edges from neighbors of endpoints of all F gates
                candidates: set[tuple[int, int]] = set()
                touched: set[int] = set()
                for gi in F:
                    a, b = twoq_pairs[gi]
                    pa, pb = layout[a], layout[b]
                    touched.add(pa)
                    touched.add(pb)
                    for nb in self.coupling.neighbors(pa):
                        x, y = int(pa), int(nb)
                        if x != y:
                            candidates.add((min(x, y), max(x, y)))
                    for nb in self.coupling.neighbors(pb):
                        x, y = int(pb), int(nb)
                        if x != y:
                            candidates.add((min(x, y), max(x, y)))

                if not candidates:
                    # Fallback: try swaps among touched phys nodes (should be rare)
                    phys_list = sorted(touched) if touched else phys_nodes[:]
                    if len(phys_list) >= 2:
                        a, b = rng.sample(phys_list, 2)
                        candidates.add((min(a, b), max(a, b)))
                    else:
                        raise RuntimeError("No candidate swaps available; coupling graph likely degenerate.")

                # Decay relaxation
                for idx in range(num_phys_nodes):
                    decay[idx] *= self.decay_lambda

                # Evaluate SABRE cost for each candidate swap (virtually)
                current_distance = dist[phys_index[layout[u]]][phys_index[layout[v]]]
                improving_edge: tuple[int, int] | None = None
                improving_cost: float = math.inf
                best_edge: tuple[int, int] | None = None
                best_cost: float = math.inf

                for a, b in candidates:
                    la = inv_layout[phys_index[a]]
                    lb = inv_layout[phys_index[b]]
                    # Virtually swap mapping
                    self._swap_mapping(layout, inv_layout, phys_index, a, b, la, lb)
                    # Distance after the hypothetical swap
                    new_distance = dist[phys_index[layout[u]]][phys_index[layout[v]]]
                    cost_front = self._cost_set(F, layout, twoq_pairs, dist, decay, phys_index)
                    cost_ext = self._cost_set(E, layout, twoq_pairs, dist, None, phys_index)
                    cost = cost_front + self.beta * cost_ext
                    # Revert
                    self._swap_mapping(layout, inv_layout, phys_index, a, b, lb, la)

                    if new_distance < current_distance:
                        if cost < improving_cost - 1e-12:
                            improving_cost = cost
                            improving_edge = (a, b)
                        elif abs(cost - improving_cost) <= 1e-12 and rng.random() < 0.5:
                            improving_edge = (a, b)

                    if cost < best_cost - 1e-12:
                        best_cost = cost
                        best_edge = (a, b)
                    elif abs(cost - best_cost) <= 1e-12 and rng.random() < 0.5:
                        best_edge = (a, b)

                # Apply chosen SWAP physically and in the mapping
                # assert best_edge is not None
                chosen_edge = improving_edge if improving_edge is not None else best_edge
                if chosen_edge is None:
                    raise RuntimeError("SABRE heuristic could not select a swap candidate.")
                a, b = chosen_edge
                out.add(SWAP(a, b))
                swap_count += 1
                la = inv_layout[phys_index[a]]
                lb = inv_layout[phys_index[b]]
                self._swap_mapping(layout, inv_layout, phys_index, a, b, la, lb)
                decay[phys_index[a]] += self.decay_delta
                decay[phys_index[b]] += self.decay_delta

            # Now adjacent: emit the mapped 2Q gate
            mapped = (layout[u], layout[v])
            out.add(self._retarget_gate(g, mapped))
            scheduled[k] = True
            # Advance front pointers for the logicals touched
            advance_front_for(u)
            advance_front_for(v)

        return out, swap_count, layout[:]

    # ----------------------- SABRE helpers -----------------------

    @staticmethod
    def _front_set(per_qubit: list[list[int]], pos: list[int], scheduled: list[bool]) -> set[int]:
        F: set[int] = set()
        for q in range(len(per_qubit)):
            L = per_qubit[q]
            i = pos[q]
            while i < len(L) and scheduled[L[i]]:
                i += 1
            if i < len(L):
                F.add(L[i])
        return F

    @staticmethod
    def _extended_set(per_qubit: list[list[int]], pos: list[int], max_size: int) -> set[int]:
        E: set[int] = set()
        if max_size <= 0:
            return E
        budget = max_size
        for q in range(len(per_qubit)):
            L = per_qubit[q]
            i = pos[q] + 1
            while i < len(L) and budget > 0:
                E.add(L[i])
                i += 1
                budget -= 1
                if budget == 0:
                    break
            if budget == 0:
                break
        return E

    @staticmethod
    def _cost_set(
        idxs: Iterable[int],
        layout: list[int],
        twoq_pairs: list[tuple[int, int]],
        dist: list[list[int]],
        decay: list[float] | None,
        phys_index: dict[int, int],
    ) -> float:
        c = 0.0
        for k in idxs:
            u, v = twoq_pairs[k]
            pu, pv = layout[u], layout[v]
            iu = phys_index[pu]
            iv = phys_index[pv]
            d = dist[iu][iv]
            if d >= 1_000_000_000:
                # Disconnected; make it very expensive
                d = 1e6  # type: ignore[assignment]
            if decay is not None:
                c += d * (1.0 + decay[iu] + decay[iv])
            else:
                c += d
        return c

    # ----------------------- structure & mapping -----------------------

    @staticmethod
    def _twoq_structure(circ: Circuit) -> tuple[list[int], list[tuple[int, int]], list[list[int]]]:
        """
        Returns:
            twoq_ops_idx: list of op indices (in circ.gates) where there is a 2Q gate
            twoq_pairs:   for each such op, the (logical) qubit pair
            per_qubit:    for each logical qubit q, list of indices into twoq_pairs that touch q
        """
        n = circ.nqubits
        twoq_ops_idx: list[int] = []
        twoq_pairs: list[tuple[int, int]] = []
        for i, g in enumerate(circ.gates):
            qs = g.qubits
            if len(qs) == 2:
                twoq_ops_idx.append(i)
                twoq_pairs.append((qs[0], qs[1]))
        per_qubit: list[list[int]] = [[] for _ in range(n)]
        for k, (u, v) in enumerate(twoq_pairs):
            per_qubit[u].append(k)
            per_qubit[v].append(k)
        return twoq_ops_idx, twoq_pairs, per_qubit

    @staticmethod
    def _invert_layout(
        layout: list[int],
        phys_index: dict[int, int],
    ) -> list[int | None]:
        inv = [None] * len(phys_index)
        for l, p in enumerate(layout):
            idx = phys_index.get(p)
            if idx is not None:
                if inv[idx] is None:
                    inv[idx] = l  # type: ignore[call-overload]
        return inv  # type: ignore[return-value]

    @staticmethod
    def _swap_mapping(
        layout: list[int],
        inv_layout: list[int | None],
        phys_index: dict[int, int],
        a: int,
        b: int,
        la: int | None,
        lb: int | None,
    ) -> None:
        # update inverse
        ia = phys_index[a]
        ib = phys_index[b]
        inv_layout[ia], inv_layout[ib] = lb, la
        # update forward
        if la is not None:
            layout[la] = b
        if lb is not None:
            layout[lb] = a

    @staticmethod
    def _apsp_unweighted(
        graph: PyGraph,
        phys_nodes: list[int],
        phys_index: dict[int, int],
    ) -> list[list[int]]:
        INF = 1_000_000_000
        dist = [[INF] * len(phys_nodes) for _ in phys_nodes]
        for s in phys_nodes:
            s = int(s)
            s_idx = phys_index[s]
            dist[s_idx][s_idx] = 0
            q = deque([s])
            seen = {s}
            while q:
                u = q.popleft()
                u = int(u)
                u_idx = phys_index[u]
                du = dist[s_idx][u_idx]
                for v in graph.neighbors(u):
                    v = int(v)
                    if v not in seen:
                        seen.add(v)
                        v_idx = phys_index[v]
                        dist[s_idx][v_idx] = du + 1
                        q.append(v)
        return dist

    def _init_layout(
        self,
        n_logical: int,
        phys_nodes: list[int],
        active_qubits: set[int],
        layout_hint: list[int] | None,
    ) -> list[int]:
        if layout_hint is not None:
            layout = list(layout_hint)
            if len(layout) > n_logical:
                layout = layout[:n_logical]
            if len(layout) < n_logical:
                used = set(layout)
                remaining = [node for node in phys_nodes if node not in used]
                placeholder = phys_nodes[0] if phys_nodes else 0
                while len(layout) < n_logical:
                    layout.append(remaining.pop(0) if remaining else placeholder)
            available = set(phys_nodes)
            active_targets = [layout[q] for q in active_qubits]
            missing = sorted({node for node in active_targets if node not in available})
            if missing:
                raise ValueError(
                    "initial_layout refers to physical qubits not present in the coupling graph for active logical "
                    f"qubits: {missing}"
                )
            if len(set(active_targets)) != len(active_targets):
                raise ValueError("initial_layout must map active logical qubits to unique physical qubits.")
            return layout
        # identity by default
        phys_set = set(phys_nodes)
        uses_physical_labels = active_qubits <= phys_set
        if uses_physical_labels:
            if not phys_nodes:
                return []
            layout = [-1] * n_logical
            for q in active_qubits:
                layout[q] = q
            placeholder = phys_nodes[0]
            for idx in range(n_logical):
                if layout[idx] == -1:
                    layout[idx] = idx if idx in phys_set else placeholder
            return layout
        if len(phys_nodes) < n_logical:
            raise ValueError(f"Coupling graph has {len(phys_nodes)} qubits but circuit needs {n_logical}.")
        return phys_nodes[:n_logical]

    # ----------------------- gate (re)construction -----------------------

    def _retarget_gate(self, g: Gate, new_qubits: tuple[int, ...]) -> Gate:
        """
        Recreate `g` on `new_qubits` using only the public API of the gate classes
        defined in this SDK.
        """
        # 1-qubit basics
        if isinstance(g, RX):
            return RX(new_qubits[0], theta=g.theta)
        if isinstance(g, RY):
            return RY(new_qubits[0], theta=g.theta)
        if isinstance(g, RZ):
            return RZ(new_qubits[0], phi=g.phi)
        if isinstance(g, U3):
            return U3(new_qubits[0], theta=g.theta, phi=g.phi, gamma=g.gamma)

        # 2-qubit basics
        if isinstance(g, CZ):
            return CZ(new_qubits[0], new_qubits[1])
        if isinstance(g, SWAP):
            return SWAP(new_qubits[0], new_qubits[1])

        # Measurement (possibly multi-qubit)
        if isinstance(g, M):
            return M(*new_qubits)

        # If you introduce more gates, add cases above.
        # Falling back to a generic reconstruction is unsafe without a uniform API.
        raise NotImplementedError(
            f"Retargeting not implemented for gate type {type(g).__name__} with arity {g.nqubits}"
        )
