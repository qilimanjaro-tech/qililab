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

from collections import deque
from typing import Mapping

from qilisdk.digital import CZ, RX, RY, RZ, SWAP, U3, Circuit, Gate, M
from rustworkx import PyGraph

from .circuit_transpiler_pass import CircuitTranspilerPass


class CustomLayoutPass(CircuitTranspilerPass):
    """
    Apply a user-specified initial layout (logical→physical mapping) and retarget
    all gates accordingly. The returned circuit is resized to the device size
    (i.e., the number of qubits of the coupling graph).

    Parameters
    ----------
    topology : PyGraph
        Undirected coupling graph whose node indices represent *physical* qubits.
        Nodes should be 0..(n_physical-1). Edges indicate allowed 2Q interactions.
    mapping : dict[int, int]
        Logical→physical mapping provided by the user. For example, for a 2-qubit
        circuit: {0: 5, 1: 2} means logical q0→phys 5, logical q1→phys 2.

    Behavior
    --------
    - Validates that `mapping` covers *every* logical qubit in the input circuit,
      is injective (no repeated physical indices), and only references physical
      qubits that exist in `topology`.
    - Stores the user-requested layout in `context.initial_layout` (same field
      set by `SabreLayoutPass`).
    - Inserts SWAPs (with corresponding un-swaps) along shortest paths of the
      coupling graph when a user-requested 2Q interaction would otherwise
      violate connectivity, keeping logical qubits on their requested physical
      nodes for subsequent operations.
    - Returns a *new* `Circuit` whose `nqubits` equals the chip size
      (len of topology's qubits) and whose gates are retargeted to the mapped
      physical qubits.
    - Exposes `last_layout` (list[int]) for diagnostics, mirroring SabreLayout.

    Notes
    -----
    * SWAPs are emitted eagerly using shortest paths whenever a 2Q gate is not
      locally executable on the chosen mapping, and are undone immediately so the
      mapping remains stable for subsequent operations.
    * ``last_layout`` matches the user-provided mapping; the same list is stored
      in ``context.initial_layout`` for diagnostics.
    """

    def __init__(self, topology: PyGraph, qubit_mapping: Mapping[int, int]) -> None:
        if not isinstance(topology, PyGraph):
            raise TypeError("CustomLayoutPass requires a rustworkx.PyGraph (undirected).")
        self.topology = topology
        # Store a copy with explicit int coercion
        self._user_mapping: dict[int, int] = {int(k): int(v) for k, v in qubit_mapping.items()}
        self.last_layout: list[int] | None = None

    # --------- public API ---------

    def run(self, circuit: Circuit) -> Circuit:
        n_logical = circuit.nqubits

        phys_nodes = list(self.topology.node_indices())
        if not phys_nodes:
            raise ValueError("Coupling graph has no nodes.")
        # As in SabreLayoutPass: assume nodes are 0..(n_physical-1)
        n_physical = max(int(x) for x in phys_nodes) + 1
        valid_phys = {int(x) for x in phys_nodes}

        # ---- validations on provided mapping ----
        keys = set(self._user_mapping.keys())
        expected = set(range(n_logical))
        if keys != expected:
            missing = sorted(expected - keys)
            extra = sorted(keys - expected)
            msg = []
            if missing:
                msg.append(f"missing logical qubits {missing}")
            if extra:
                msg.append(f"extraneous logical keys {extra}")
            raise ValueError(
                "User mapping must map *every* logical qubit in the circuit exactly once; " + "; ".join(msg)
            )

        values = list(self._user_mapping.values())
        if len(set(values)) != len(values):
            # find duplicates for a clearer error
            seen: set[int] = set()
            dups: list[int] = []
            for v in values:
                if v in seen:
                    dups.append(v)
                else:
                    seen.add(v)
            dups.sort()
            raise ValueError(f"User mapping is not injective; duplicated physical qubits: {dups}")

        out_of_range = sorted(set(values) - valid_phys)
        if out_of_range:
            raise ValueError(f"Mapping refers to physical qubits not present in the coupling graph: {out_of_range}")

        # Build the layout list[int] where layout[logical] = physical and keep a copy for diagnostics
        layout = [self._user_mapping[q] for q in range(n_logical)]
        initial_layout = layout[:]

        # Track which logical qubit currently occupies each physical node
        inv_layout: list[int | None] = [None] * n_physical
        for logical, phys in enumerate(layout):
            inv_layout[phys] = logical

        # Retarget gates, inserting SWAPs along shortest paths whenever a 2Q interaction
        # would otherwise violate the coupling constraints. SWAPs are added in pairs so
        # that the logical-to-physical mapping is restored after each routed 2Q gate.
        new_circuit = Circuit(n_physical)

        for gate in circuit.gates:
            qubits = gate.qubits

            if len(qubits) <= 1 or isinstance(gate, M):
                mapped = tuple(layout[q] for q in qubits)
                new_circuit.add(self._retarget_gate(gate, mapped))
                continue

            if len(qubits) != 2:
                raise NotImplementedError(
                    f"CustomLayoutPass currently supports routing for 1Q/2Q gates only; "
                    f"received {type(gate).__name__} acting on {len(qubits)} qubits."
                )

            u, v = qubits

            if self.topology.has_edge(layout[u], layout[v]):
                mapped = (layout[u], layout[v])
                new_circuit.add(self._retarget_gate(gate, mapped))
                continue

            path = self._shortest_path(layout[u], layout[v])
            if path is None or len(path) < 2:
                raise ValueError(
                    "User mapping cannot be routed on the provided topology; no path between "
                    f"physical qubits {layout[u]} and {layout[v]}."
                )

            applied_swaps: list[tuple[int, int]] = []
            # Move the second qubit along the path until it neighbors the first one.
            for i in range(len(path) - 1, 1, -1):
                a, b = path[i - 1], path[i]
                new_circuit.add(SWAP(a, b))
                self._apply_swap_to_layout(layout, inv_layout, a, b)
                applied_swaps.append((a, b))

            mapped = (layout[u], layout[v])
            if not self.topology.has_edge(*mapped):
                raise RuntimeError(
                    "Failed to route gate after inserting swaps; resulting qubits are still non-adjacent."
                )
            new_circuit.add(self._retarget_gate(gate, mapped))

            # Restore the original mapping so later 1Q gates remain on the requested qubits.
            for a, b in reversed(applied_swaps):
                new_circuit.add(SWAP(a, b))
                self._apply_swap_to_layout(layout, inv_layout, a, b)

        # Record diagnostics: final layout after routing and expose the user-requested layout in context.
        self.last_layout = layout[:]

        if self.context is not None:
            self.context.initial_layout = initial_layout
            self.context.final_layout = list(range(self.topology.num_nodes()))

        self.append_circuit_to_context(new_circuit)

        return new_circuit

    # --------- retargeting helpers (mirrors SabreLayoutPass) ---------

    def _retarget_gate(self, g: Gate, new_qubits: tuple[int, ...]) -> Gate:
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

        raise NotImplementedError(
            f"Retargeting not implemented for gate type {type(g).__name__} with arity {g.nqubits}"
        )

    def _apply_swap_to_layout(
        self,
        layout: list[int],
        inv_layout: list[int | None],
        phys_a: int,
        phys_b: int,
    ) -> None:
        """Update layout/inverse-layout mappings after inserting a SWAP(phys_a, phys_b)."""

        logical_a = inv_layout[phys_a]
        logical_b = inv_layout[phys_b]

        inv_layout[phys_a], inv_layout[phys_b] = logical_b, logical_a

        if logical_a is not None:
            layout[logical_a] = phys_b
        if logical_b is not None:
            layout[logical_b] = phys_a

    def _shortest_path(self, start: int, goal: int) -> list[int] | None:
        """Return a shortest path between `start` and `goal` physical qubits."""

        if start == goal:
            return [start]

        visited = {start}
        parents: dict[int, int] = {}
        queue: deque[int] = deque([start])

        while queue:
            node = queue.popleft()
            for nb in self.topology.neighbors(node):
                nb = int(nb)
                if nb in visited:
                    continue
                parents[nb] = node
                if nb == goal:
                    path = [goal]
                    while path[-1] != start:
                        path.append(parents[path[-1]])
                    path.reverse()
                    return path
                visited.add(nb)
                queue.append(nb)

        return None
