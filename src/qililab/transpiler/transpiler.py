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

from qililab.transpiler.gate_decompositions import translate_gates

from .native_gates import Drag


def translate_circuit(circuit: Circuit, optimize: bool = False) -> Circuit:
    """Converts circuit with qibo gates to circuit with native gates

    Args:
        circuit (Circuit): circuit with qibo gates
        optimize (bool): optimize the transpiled circuit using otpimize_transpilation

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
        new_circuit.add(optimize_transpilation(circuit.nqubits, gates_to_optimize))
    else:
        new_circuit.add(translate_gates(ngates))

    return new_circuit


def optimize_transpilation(nqubits: int, ngates: list[gates.Gate]) -> list[gates.Gate]:
    """Optimizes transpiled circuit by moving all RZ to the left of all operators as a single RZ
    This RZ can afterwards be removed since the next operation is going to be a measurement,
    which happens on the Z basis and is therefore invariant under rotations around the Z axis

    Mind that moving an operator to the left is equivalent to applying this operator last so
    it is actually moved to the _right_ of Circuit.queue (last element of list)

    Args:
        nqubits (int) : number of qubits in the circuit
        ngates (list[gates.Gate]) : list of gates in the circuit

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
        else:
            # if gate is drag pulse, shift parameters by accumulated Zs
            if isinstance(gate, Drag):
                # create new drag pulse rather than modify parameters of the old one
                gate = Drag(gate.qubits[0], gate.parameters[0], gate.parameters[1] - shift[gate.qubits[0]])

            # append gate to optimized list
            new_gates.append(gate)

    return new_gates
