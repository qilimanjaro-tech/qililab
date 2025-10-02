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

from typing import TYPE_CHECKING, Optional, Union

from qilisdk.digital import Circuit
from qilisdk.digital.gates import CZ, RZ, M

from qililab.digital.native_gates import Drag

from .circuit_transpiler_pass import CircuitTranspilerPass

if TYPE_CHECKING:
    from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings
    from qililab.settings.digital.gate_event_settings import GateEventSettings


class AddPhasesToDragsFromRZAndCZPass(CircuitTranspilerPass):
    """This pass adds the phases from RZs and CZs gates of the circuit to the next Drag gates.

        - The CZs added phases on the Drags, come from a correction from their calibration, stored on the setting of the CZs.
        - The RZs added phases on the Drags, come from commuting all the RZs all the way to the end of the circuit, so they can be deleted as "virtual Z gates".

    This is done by moving all RZ to the left of all operators as a single RZ. The corresponding cumulative rotation
    from each RZ is carried on as phase in all drag pulses left of the RZ operator.

    Virtual Z gates are also applied to correct phase errors from CZ gates.

    The final RZ operator left to be applied as the last operator in the circuit can afterwards be removed since the last
    operation is going to be a measurement, which is performed on the Z basis and is therefore invariant under rotations
    around the Z axis.

    This last step can also be seen from the fact that an RZ operator applied on a single qubit, with no operations carried
    on afterwards induces a phase rotation. Since phase is an imaginary unitary component, its absolute value will be 1
    independent on any (unitary) operations carried on it.

    Mind that moving an operator to the left is equivalent to applying this operator last so
    it is actually moved to the _right_ of ``Circuit.queue`` (last element of list).

    For more information on virtual Z gates, see https://arxiv.org/abs/1612.00858
    """

    def __init__(self, settings: DigitalCompilationSettings) -> None:
        self._settings = settings

    def run(self, circuit: Circuit) -> Circuit:
        nqubits = circuit.nqubits
        circuit_gates = circuit.gates

        out_circuit = Circuit(nqubits)
        shift = dict.fromkeys(range(nqubits), 0.0)

        for gate in circuit_gates:
            out_gate: Optional[Union[M, Drag, CZ]] = None

            # Accumulate phase shifts from commutating RZ to the end, to discard them as VirtualZ.
            if isinstance(gate, RZ):
                shift[gate.target_qubits[0]] += gate.phi

            # Accumulate phase shifts from the phase corrections of the CZs, and leave CZs unchanged.
            elif isinstance(gate, CZ):
                control_qubit, target_qubit = gate.control_qubits[0], gate.target_qubits[0]  # Assumes 2 qubits
                gate_settings = self._settings.get_gate(name="CZ", qubits=(control_qubit, target_qubit))
                gate_corrections = self._extract_gate_corrections(gate_settings, control_qubit)
                if gate_corrections is not None:
                    shift[control_qubit] += gate_corrections[f"q{control_qubit}_phase_correction"]
                    shift[target_qubit] += gate_corrections[f"q{target_qubit}_phase_correction"]
                out_gate = CZ(control_qubit, target_qubit)

            # Correct Drag phase with accumulated phase shifts.
            elif isinstance(gate, Drag):
                qubit: int = gate.qubits[0]  # Assumes single qubit
                out_gate = Drag(qubit, theta=gate.theta, phase=(gate.phase - shift[qubit]))

            # Measurement gates, do not change
            elif isinstance(gate, M):
                out_gate = M(*gate.qubits)

            # If gate is not supported, raise an error
            else:
                raise ValueError(f"{gate.name} not part of native supported gates {(RZ, Drag, CZ, M)}")

            # Add the processed gate to the output circuit
            if out_gate is not None:
                out_circuit.add(out_gate)

        return out_circuit

    @staticmethod
    def _extract_gate_corrections(gate_settings: list[GateEventSettings], control_qubit: int) -> dict | None:
        """Given a CZ gate settings, extract the phase corrections needed for its control and target qubits."""
        return next(
            (
                event.pulse.options
                for event in gate_settings
                if event.pulse.options is not None and f"q{control_qubit}_phase_correction" in event.pulse.options
            ),
            None,
        )
