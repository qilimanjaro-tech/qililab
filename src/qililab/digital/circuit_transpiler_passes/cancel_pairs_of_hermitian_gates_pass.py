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


from typing import ClassVar

from qilisdk.digital import CNOT, CZ, SWAP, Circuit, Gate, H, X, Y, Z
from qilisdk.digital.gates import Adjoint, Controlled, Modified

from .circuit_transpiler_pass import CircuitTranspilerPass


class CancelPairsOfHermitianGatesPass(CircuitTranspilerPass):
    """
    Remove pairs of Hermitian gates that act on the same qubits.

    Rules:
      - A gate is considered Hermitian *only* if its type (or its underlying
        basic gate type, for Modified gates) is in `hermitian_gates`.
      - Two identical Hermitian gates on the same qubits cancel.
      - Intervening operations on disjoint qubits do not block cancellation.
      - Any operation that touches any of the same qubits blocks cancellation
        across it.
      - Runs to a fixed point.

    Notes:
      - If you want controlled versions of Hermitian gates to be considered
        Hermitian, either add their concrete classes (e.g. `CNOT`, `CZ`) to
        `hermitian_gates`, or rely on the recursion over `Modified` which
        treats a `Modified` gate as Hermitian when its `basic_gate` type is
        in the set.
    """
    hermitian_gates: ClassVar[set[type[Gate]]] = {H, X, Y, Z, CNOT, CZ, SWAP}

    def run(self, circuit: Circuit) -> Circuit:
        while True:
            # Stack of unmatched Hermitian candidates:
            #   key = (semantic_kind, qubits_tuple) -> index in circuit.gates
            stack: dict[tuple[object, tuple[int, ...]], int] = {}

            # Indices to delete this round (collect, then delete in reverse order)
            to_delete: set[int] = set()

            for idx, gate in enumerate(circuit.gates):
                qubits = gate.qubits

                if self._is_hermitian(gate):
                    key = (self._semantic_key(gate), qubits)

                    if key in stack:
                        # Found a commuting-adjacent identical Hermitian gate; cancel the pair.
                        prev_idx = stack.pop(key)
                        to_delete.add(prev_idx)
                        to_delete.add(idx)
                        # Do not push current gate; both will be removed.
                        continue

                    # No match: this gate becomes the latest candidate, but first
                    # block older candidates that share any qubit.
                    self._block_overlapping(stack, qubits)
                    stack[key] = idx
                else:
                    # Non-Hermitian operations block across the qubits they touch.
                    self._block_overlapping(stack, qubits)

            if not to_delete:
                break  # fixed point reached

            # Perform in-place deletions on circuit.gates (reverse order to keep indices valid)
            for j in sorted(to_delete, reverse=True):
                del circuit.gates[j]

        return circuit

    # ----------------- helpers -----------------

    def _is_hermitian(self, gate: Gate) -> bool:
        """Hermitian iff its type is listed, or (recursively) its basic_gate's type is listed."""
        if type(gate) in self.hermitian_gates:
            return True
        if isinstance(gate, Modified):
            return self._is_hermitian(gate.basic_gate)
        return False
    
    def _semantic_key(self, gate: Gate) -> object:
        """
        Canonical identity for matching cancellations.
        - Adjoint of a Hermitian gate normalizes to the base gate key.
        - Controlled normalizes to (“Controlled”, n_controls, base_key).
        - Plain gates use their concrete class.
        """
        if isinstance(gate, Adjoint):
            return self._semantic_key(gate.basic_gate)
        if isinstance(gate, Controlled):
            return ("Controlled", len(gate.control_qubits), self._semantic_key(gate.basic_gate))
        return type(gate)

    @staticmethod
    def _block_overlapping(
        stack: dict[tuple[object, tuple[int, ...]], int],
        qubits: tuple[int, ...],
    ) -> None:
        """Drop any candidate whose qubits overlap with `qubits`."""
        if not qubits:
            stack.clear()
            return
        touched = set(qubits)
        for k in list(stack.keys()):
            _, k_qubits = k
            if touched.intersection(k_qubits):
                stack.pop(k, None)
