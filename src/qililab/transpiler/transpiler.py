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

"""This file contains the functions used to decompose a circuit into native gates and to compute virtual-Z gates."""
from qibo import gates
from qibo.models import Circuit

from qililab.settings.runcard import Runcard
from qililab.transpiler.gate_decompositions import translate_gates

from .native_gates import Drag


def translate_circuit(
    circuit: Circuit, gates_settings: Runcard.GatesSettings | None = None, optimize: bool = True
) -> Circuit:
    """Converts circuit with qibo gates to circuit with native gates

    Args:
        circuit (Circuit): circuit with qibo gates
        optimize (bool): optimize the transpiled circuit using otpimize_transpilation
        gates_settings (Runcard.GatesSettings): calibrated gate settings from the runcard. This is used only for phase correction in CZ gates

    Returns:
        new_circuit (Circuit): circuit with transpiled gates
    """
    # get list of gates from circuit
    ngates = circuit.queue
    # init new circuit
    new_circuit = Circuit(circuit.nqubits)
    # add transpiled gates to new circuit, optimize if needed
    if optimize:
        gates_to_optimize = translate_gates(ngates)
        new_circuit.add(
            optimize_transpilation(circuit.nqubits, ngates=gates_to_optimize, gates_settings=gates_settings)
        )
    else:
        new_circuit.add(translate_gates(ngates))

    return new_circuit


def optimize_transpilation(
    nqubits: int, ngates: list[gates.Gate], gates_settings: Runcard.GatesSettings | None = None
) -> list[gates.Gate]:
    """Optimizes transpiled circuit by applying virtual Z gates.
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
    it is actually moved to the _right_ of Circuit.queue (last element of list).

    For more information on virtual Z gates, see https://arxiv.org/abs/1612.00858

    Args:
        nqubits (int) : number of qubits in the circuit
        ngates (list[gates.Gate]) : list of gates in the circuit
        gates_settings (Runcard.GatesSettings): calibrated gate settings from the runcard. This is used only for phase correction in CZ gates

    Returns:
        list[gates.Gate] : list of re-ordered gates
    """
    supported_gates = ["rz", "drag", "cz", "measure"]
    new_gates = []
    shift = {qubit: 0 for qubit in range(nqubits)}
    for gate in ngates:
        if gate.name not in supported_gates:
            raise NotImplementedError(f"{gate.name} not part of supported gates {supported_gates}")
        if isinstance(gate, gates.RZ):
            shift[gate.qubits[0]] += gate.parameters[0]
        # add CZ phase correction
        elif isinstance(gate, gates.CZ) and gates_settings is not None:
            gate_settings = gates_settings.get_gate(name=gate.__class__.__name__, qubits=gate.qubits)
            control_qubit, target_qubit = gate.qubits
            corrections = next(
                (
                    event.pulse.options
                    for event in gate_settings
                    if (event.pulse.options is not None and f"q{control_qubit}_phase_correction" in event.pulse.options)
                ),
                None,
            )
            if corrections is not None:
                shift[control_qubit] += corrections[f"q{control_qubit}_phase_correction"]
                shift[target_qubit] += corrections[f"q{target_qubit}_phase_correction"]
            new_gates.append(gate)
        else:
            # if gate is drag pulse, shift parameters by accumulated Zs
            if isinstance(gate, Drag):
                # create new drag pulse rather than modify parameters of the old one
                gate = Drag(gate.qubits[0], gate.parameters[0], gate.parameters[1] - shift[gate.qubits[0]])

            # append gate to optimized list
            new_gates.append(gate)

    return new_gates
