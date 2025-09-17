from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from collections import deque
from copy import deepcopy
from typing import ClassVar, Iterable

import rustworkx as rx
from qilisdk.digital import (
    CNOT,
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    Circuit,
    Gate,
    H,
    I,
    M,
    S,
    T,
    X,
    Y,
    Z,
)
from qilisdk.digital.gates import Adjoint, BasicGate, Controlled, Exponential, Modified
from rustworkx import PyGraph

from .circuit_transpiler_pass import CircuitTranspilerPass


class SabreSwapPass(CircuitTranspilerPass):
    """
    SABRE routing (SWAP insertion) for 1Q/2Q circuits on an undirected coupling graph.

    Inputs
    ------
    coupling : rustworkx.PyGraph
        Undirected device graph. Node indices are physical qubits.
    initial_layout : list[int] | None
        Logical -> physical mapping to start from (e.g., from SabreLayoutPass.last_layout).
        If None, uses identity mapping [0, 1, 2, ...].

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

    hermitian_gates: ClassVar[set[type[Gate]]] = set()  # not used here

    def __init__(
        self,
        coupling: PyGraph,
        *,
        initial_layout: list[int] | None = None,
        seed: int | None = None,
        lookahead_size: int = 10,
        beta: float = 0.5,
        decay_delta: float = 0.001,
        decay_lambda: float = 0.99,
        max_swaps_factor: float = 8.0,
    ) -> None:
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

        # Diagnostics
        self.last_swap_count: int | None = None
        self.last_final_layout: list[int] | None = None

    # ----------------------- public API -----------------------

    def run(self, circuit: Circuit) -> Circuit:
        rng = random.Random(self.seed)

        n_logical = circuit.nqubits
        phys_nodes = list(self.coupling.node_indices())
        if not phys_nodes:
            raise ValueError("Coupling graph has no nodes.")
        n_physical = max(int(x) for x in phys_nodes) + 1

        layout = self._init_layout(n_logical, n_physical)
        inv_layout = self._invert_layout(layout, n_physical)
        dist = self._apsp_unweighted(self.coupling, n_physical)

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
        out_n = max(n_physical, max(layout) + 1 if layout else n_physical)
        out = Circuit(out_n)

        # Decay penalties on physical qubits
        decay = [0.0] * n_physical
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
            max_swaps_this_gate = int(self.max_swaps_factor * max(1, dist[layout[u]][layout[v]]))
            steps = 0
            while dist[layout[u]][layout[v]] != 1:
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
                    touched.add(pa); touched.add(pb)
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
                    phys_list = sorted(touched) if touched else list(range(n_physical))
                    if len(phys_list) >= 2:
                        a, b = rng.sample(phys_list, 2)
                        candidates.add((min(a, b), max(a, b)))
                    else:
                        raise RuntimeError("No candidate swaps available; coupling graph likely degenerate.")

                # Decay relaxation
                for i in range(n_physical):
                    decay[i] *= self.decay_lambda

                # Evaluate SABRE cost for each candidate swap (virtually)
                best_edge: tuple[int, int] | None = None
                best_cost: float = math.inf

                for a, b in candidates:
                    la, lb = inv_layout[a], inv_layout[b]
                    # Virtually swap mapping
                    self._swap_mapping(layout, inv_layout, a, b, la, lb)
                    cost_front = self._cost_set(F, layout, twoq_pairs, dist, decay)
                    cost_ext = self._cost_set(E, layout, twoq_pairs, dist, None)
                    cost = cost_front + self.beta * cost_ext
                    # Revert
                    self._swap_mapping(layout, inv_layout, a, b, lb, la)

                    if cost < best_cost - 1e-12:
                        best_cost = cost
                        best_edge = (a, b)
                    elif abs(cost - best_cost) <= 1e-12 and rng.random() < 0.5:
                        best_edge = (a, b)

                # Apply chosen SWAP physically and in the mapping
                assert best_edge is not None
                a, b = best_edge
                out.add(SWAP(a, b))
                swap_count += 1
                la, lb = inv_layout[a], inv_layout[b]
                self._swap_mapping(layout, inv_layout, a, b, la, lb)
                decay[a] += self.decay_delta
                decay[b] += self.decay_delta

            # Now adjacent: emit the mapped 2Q gate
            mapped = (layout[u], layout[v])
            out.add(self._retarget_gate(g, mapped))
            scheduled[k] = True
            # Advance front pointers for the logicals touched
            advance_front_for(u)
            advance_front_for(v)

        self.last_swap_count = swap_count
        self.last_final_layout = layout[:]  # mapping at the end of routing
        return out

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
    ) -> float:
        c = 0.0
        for k in idxs:
            u, v = twoq_pairs[k]
            pu, pv = layout[u], layout[v]
            d = dist[pu][pv]
            if d >= 1_000_000_000:
                # Disconnected; make it very expensive
                d = 1e6
            if decay is not None:
                c += d * (1.0 + decay[pu] + decay[pv])
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
    def _invert_layout(layout: list[int], n_physical: int) -> list[int | None]:
        inv = [None] * n_physical
        for l, p in enumerate(layout):
            if 0 <= p < n_physical:
                inv[p] = l
        return inv

    @staticmethod
    def _swap_mapping(
        layout: list[int],
        inv_layout: list[int | None],
        a: int, b: int,
        la: int | None, lb: int | None,
    ) -> None:
        # update inverse
        inv_layout[a], inv_layout[b] = lb, la
        # update forward
        if la is not None:
            layout[la] = b
        if lb is not None:
            layout[lb] = a

    @staticmethod
    def _apsp_unweighted(graph: PyGraph, n_physical: int) -> list[list[int]]:
        INF = 1_000_000_000
        dist = [[INF] * n_physical for _ in range(n_physical)]
        for s in graph.node_indices():
            s = int(s)
            dist[s][s] = 0
            q = deque([s])
            seen = {s}
            while q:
                u = q.popleft()
                du = dist[s][u]
                for v in graph.neighbors(u):
                    v = int(v)
                    if v not in seen:
                        seen.add(v)
                        dist[s][v] = du + 1
                        q.append(v)
        return dist

    def _init_layout(self, n_logical: int, n_physical: int) -> list[int]:
        if self.initial_layout is not None:
            if len(self.initial_layout) != n_logical:
                raise ValueError(
                    f"initial_layout length {len(self.initial_layout)} != circuit.nqubits {n_logical}"
                )
            return list(self.initial_layout)
        # identity by default
        if n_physical < n_logical:
            raise ValueError(
                f"Coupling graph has {n_physical} qubits but circuit needs {n_logical}."
            )
        return list(range(n_logical))

    # ----------------------- gate (re)construction -----------------------

    def _retarget_gate(self, g: Gate, new_qubits: tuple[int, ...]) -> Gate:
        """
        Recreate `g` on `new_qubits` using only the public API of the gate classes
        defined in this SDK.
        """
        # 1-qubit basics
        if isinstance(g, I):
            return I(new_qubits[0])
        if isinstance(g, X):
            return X(new_qubits[0])
        if isinstance(g, Y):
            return Y(new_qubits[0])
        if isinstance(g, Z):
            return Z(new_qubits[0])
        if isinstance(g, H):
            return H(new_qubits[0])
        if isinstance(g, S):
            return S(new_qubits[0])
        if isinstance(g, T):
            return T(new_qubits[0])
        if isinstance(g, RX):
            return RX(new_qubits[0], theta=g.theta)
        if isinstance(g, RY):
            return RY(new_qubits[0], theta=g.theta)
        if isinstance(g, RZ):
            return RZ(new_qubits[0], phi=g.phi)
        if isinstance(g, U1):
            return U1(new_qubits[0], phi=g.phi)
        if isinstance(g, U2):
            return U2(new_qubits[0], phi=g.phi, gamma=g.gamma)
        if isinstance(g, U3):
            return U3(new_qubits[0], theta=g.theta, phi=g.phi, gamma=g.gamma)

        # 2-qubit basics
        if isinstance(g, CNOT):
            return CNOT(new_qubits[0], new_qubits[1])
        if isinstance(g, CZ):
            return CZ(new_qubits[0], new_qubits[1])
        if isinstance(g, SWAP):
            return SWAP(new_qubits[0], new_qubits[1])

        # Measurement (possibly multi-qubit)
        if isinstance(g, M):
            return M(*new_qubits)

        # Generic Modified gates
        if isinstance(g, Adjoint):
            return Adjoint(self._retarget_gate(g.basic_gate, new_qubits))
        if isinstance(g, Exponential):
            return Exponential(self._retarget_gate(g.basic_gate, new_qubits))
        if isinstance(g, Controlled):
            n_ctrl = len(g.control_qubits)
            controls = new_qubits[:n_ctrl]
            targets = new_qubits[n_ctrl:]
            retargeted_basic = self._retarget_gate(g.basic_gate, targets)
            return Controlled(*controls, basic_gate=retargeted_basic)

        # If you introduce more gates, add cases above.
        # Falling back to a generic reconstruction is unsafe without a uniform API.
        raise NotImplementedError(
            f"Retargeting not implemented for gate type {type(g).__name__} with arity {g.nqubits}"
        )
