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
    - Sets `context.initial_layout` to the final list[int] mapping (same field
      set by `SabreLayoutPass`).
    - Returns a *new* `Circuit` whose `nqubits` equals the chip size
      (len of topology's qubits) and whose gates are retargeted to the mapped
      physical qubits.
    - Exposes `last_layout` (list[int]) for diagnostics, mirroring SabreLayout.

    Notes
    -----
    * This pass performs **layout only**; it does not check connectivity or
      insert SWAPs. Use a routing pass afterwards if needed.
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
            raise ValueError(
                f"Mapping refers to physical qubits not present in the coupling graph: {out_of_range}"
            )

        # Build the layout list[int] where layout[logical] = physical
        layout = [self._user_mapping[q] for q in range(n_logical)]
        self.last_layout = layout

        # Expose initial layout in the shared context (same behavior as Sabre)
        if self.context is not None:
            self.context.initial_layout = layout

        # Retarget to the chosen layout and **resize to chip size**.
        new_circuit = self._retarget_circuit_to_device_size(circuit, layout, n_physical)

        # Keep the transformed circuit in the pass context history, like other passes
        self.append_circuit_to_context(new_circuit)

        return new_circuit

    # --------- retargeting helpers (mirrors SabreLayoutPass) ---------

    def _retarget_circuit_to_device_size(
        self, circuit: Circuit, layout: list[int], n_physical: int
    ) -> Circuit:
        """
        Create a new Circuit with size equal to the device (`n_physical`)
        and all gates remapped according to `layout`.
        """
        new_circ = Circuit(n_physical)
        for g in circuit.gates:
            mapped_qubits = tuple(layout[q] for q in g.qubits)
            new_circ.add(self._retarget_gate(g, mapped_qubits))
        return new_circ

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
