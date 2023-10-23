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

"""This file contains the needed classes/methods to decompose gates into native gates."""
from collections.abc import Callable

import numpy as np
from qibo import gates

from .native_gates import Drag, Wait


class GateDecompositions:
    """Abstract data structure that holds decompositions of gates."""

    def __init__(self):
        self.decompositions = {}

    def add(self, gate: gates.Gate, decomposition: list[gates.Gate] | Callable[[gates.Gate], list[gates.Gate]]):
        """Register a decomposition for a gate. Note that the decomposition list can have
        non-native gates

        Args:
            gate (gates.Gate): gate to be decomposed
            decomposition (list(gates.Gate)): list of gates for the decomposition

        """
        self.decompositions[gate] = decomposition

    def __call__(self, gate: gates.Gate) -> list[gates.Gate]:
        """Decompose a gate into native gates

        Args:
            gate (gates.Gate): gate to decompose

        Returns:
            list[gates.Gate]: list of gates corresponding to the decomposition of the given gate
        """

        # check that a decomposition exists
        if type(gate) not in self.decompositions:
            raise NotImplementedError(
                f"Gate of type {gate.__class__} is not supported for transpilation. "
                "Supported gates are {self.decompositions.keys()}"
            )

        decomposition = self.decompositions[gate.__class__]
        if callable(decomposition):
            decomposition = decomposition(gate)
        return [g.on_qubits(dict(enumerate(gate.qubits))) for g in decomposition]


def translate_gates(ngates: list[gates.Gate]) -> list[gates.Gate]:
    """Maps Qibo gates to a hardware native implementation (CZ, RZ, Drag, Wait and M (Measurement))
    - CZ gates are our 2 qubit gates
    - RZ gates are applied as virtual Z gates if optimize=True in the transpiler
    - Drag gates are our single qubit gates
    - Wait gates add wait time at a single qubit
    - Measurement gates measure the circuit

    Args:
        ngates (list[gates.Gate]): list of gates to be decomposed.

    Returns:
        list[gates.Gate]: list of native gates corresponding to input gates
    """

    # define supported gates (native qpu gates + virtual z + measurement)
    supported_gates = native_gates() + (gates.RZ, gates.M, Wait)

    # check which gates are native gates and if not all of them are so, translate
    to_translate = [not isinstance(gate, supported_gates) for gate in ngates]

    new_gates = []
    # iterate through all gates
    if sum(to_translate) != 0:
        for gate, tt in zip(ngates, to_translate):
            if not tt:
                new_gates.append(gate)  # append already native gates
            # distinguish 1 or 2 qubit gates
            else:
                new_gates += qili_dec(gate)
        return translate_gates(new_gates)
    return ngates


def native_gates():
    """List of native hardware gates

    Returns:
        tuple[gates.Gate]: Hardware native gates
    """
    return (Drag, gates.CZ)


# Mind that the order of the gates is "the inverse" of the operators
# i.e. to perform the operation AB|psi> the order of the operators
# returned as a list must be  [B, A] so that B is applied to |psi> 1st
qili_dec = GateDecompositions()
qili_dec.add(gates.I, [gates.RZ(0, 0)])
qili_dec.add(gates.H, [Drag(0, np.pi / 2, -np.pi / 2), gates.RZ(0, np.pi)])
qili_dec.add(gates.X, [Drag(0, np.pi, 0)])
qili_dec.add(
    gates.Y,
    [
        Drag(0, np.pi, 0),
        gates.RZ(0, np.pi),
    ],
)
qili_dec.add(gates.Z, [gates.RZ(0, np.pi)])

qili_dec.add(gates.RX, lambda gate: [Drag(0, gate.parameters[0], 0)])
qili_dec.add(gates.RY, lambda gate: [Drag(0, gate.parameters[0], np.pi / 2)])
qili_dec.add(gates.RZ, lambda gate: [gates.RZ(0, gate.parameters[0] / 2)])
qili_dec.add(gates.U1, lambda gate: [gates.RZ(0, gate.parameters[0])])
qili_dec.add(gates.U2, lambda gate: [gates.U3(0, np.pi / 2, gate.parameters[0], gate.parameters[1])])
qili_dec.add(
    gates.U3,
    lambda gate: [
        Drag(0, gate.parameters[0], -gate.parameters[2] + np.pi / 2),  # qibo's U3 is different from standard U3
        gates.RZ(0, gate.parameters[1] + gate.parameters[2]),
    ],
)
qili_dec.add(gates.S, [gates.RZ(0, np.pi / 2)])
qili_dec.add(gates.SDG, [gates.RZ(0, -np.pi / 2)])
qili_dec.add(gates.T, [gates.RZ(0, np.pi / 4)])
qili_dec.add(gates.TDG, [gates.RZ(0, -np.pi / 4)])

# register CZ decompositions
qili_dec.add(gates.CNOT, [gates.H(1), gates.CZ(0, 1), gates.H(1)])
qili_dec.add(gates.CZ, [gates.CZ(0, 1)])
qili_dec.add(
    gates.SWAP,
    [
        gates.H(1),
        gates.CZ(0, 1),
        gates.H(1),
        gates.H(0),
        gates.CZ(1, 0),
        gates.H(0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.H(1),
    ],
)
qili_dec.add(
    gates.iSWAP,
    [
        gates.U3(0, np.pi / 2.0, 0, -np.pi / 2.0),
        gates.U3(1, np.pi / 2.0, 0, -np.pi / 2.0),
        gates.CZ(0, 1),
        gates.H(0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.H(0),
        gates.H(1),
    ],
)
qili_dec.add(
    gates.CRX,
    lambda gate: [
        gates.RX(1, gate.parameters[0] / 2.0),
        gates.CZ(0, 1),
        gates.RX(1, -gate.parameters[0] / 2.0),
        gates.CZ(0, 1),
    ],
)
qili_dec.add(
    gates.CRY,
    lambda gate: [
        gates.RY(1, gate.parameters[0] / 2.0),
        gates.CZ(0, 1),
        gates.RY(1, -gate.parameters[0] / 2.0),
        gates.CZ(0, 1),
    ],
)
qili_dec.add(
    gates.CRZ,
    lambda gate: [
        gates.RZ(1, gate.parameters[0] / 2.0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.RX(1, -gate.parameters[0] / 2.0),
        gates.CZ(0, 1),
        gates.H(1),
    ],
)
qili_dec.add(
    gates.CU1,
    lambda gate: [
        gates.RZ(0, gate.parameters[0] / 2.0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.RX(1, -gate.parameters[0] / 2.0),
        gates.CZ(0, 1),
        gates.H(1),
        gates.RZ(1, gate.parameters[0] / 2.0),
    ],
)
qili_dec.add(
    gates.CU2,
    lambda gate: [
        gates.RZ(1, (gate.parameters[1] - gate.parameters[0]) / 2.0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.H(1),
        gates.U3(1, -np.pi / 4, 0, -(gate.parameters[1] + gate.parameters[0]) / 2.0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.H(1),
        gates.U3(1, np.pi / 4, gate.parameters[0], 0),
    ],
)
qili_dec.add(
    gates.CU3,
    lambda gate: [
        gates.RZ(1, (gate.parameters[2] - gate.parameters[1]) / 2.0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.H(1),
        gates.U3(1, -gate.parameters[0] / 2.0, 0, -(gate.parameters[2] + gate.parameters[1]) / 2.0),
        gates.H(1),
        gates.CZ(0, 1),
        gates.H(1),
        gates.U3(1, gate.parameters[0] / 2.0, gate.parameters[1], 0),
    ],
)
qili_dec.add(
    gates.FSWAP,
    [
        gates.U3(0, np.pi / 2, -np.pi / 2, -np.pi),
        gates.U3(1, np.pi / 2, np.pi / 2, np.pi / 2),
        gates.CZ(0, 1),
        gates.U3(0, np.pi / 2, 0, -np.pi / 2),
        gates.U3(1, np.pi / 2, 0, np.pi / 2),
        gates.CZ(0, 1),
        gates.U3(0, np.pi / 2, np.pi / 2, -np.pi),
        gates.U3(1, np.pi / 2, 0, -np.pi),
    ],
)
qili_dec.add(
    gates.RXX,
    lambda gate: [
        gates.H(0),
        gates.CZ(0, 1),
        gates.RX(1, gate.parameters[0]),
        gates.CZ(0, 1),
        gates.H(0),
    ],
)
qili_dec.add(
    gates.RYY,
    lambda gate: [
        gates.RX(0, np.pi / 2),
        gates.U3(1, np.pi / 2, np.pi / 2, -np.pi),
        gates.CZ(0, 1),
        gates.RX(1, gate.parameters[0]),
        gates.CZ(0, 1),
        gates.RX(0, -np.pi / 2),
        gates.U3(1, np.pi / 2, 0, np.pi / 2),
    ],
)
qili_dec.add(
    gates.RZZ,
    lambda gate: [
        gates.H(1),
        gates.CZ(0, 1),
        gates.RX(1, gate.parameters[0]),
        gates.CZ(0, 1),
        gates.H(1),
    ],
)
qili_dec.add(
    gates.TOFFOLI,
    [
        gates.CZ(1, 2),
        gates.RX(2, -np.pi / 4),
        gates.CZ(0, 2),
        gates.RX(2, np.pi / 4),
        gates.CZ(1, 2),
        gates.RX(2, -np.pi / 4),
        gates.CZ(0, 2),
        gates.RX(2, np.pi / 4),
        gates.RZ(1, np.pi / 4),
        gates.H(1),
        gates.CZ(0, 1),
        gates.RZ(0, np.pi / 4),
        gates.RX(1, -np.pi / 4),
        gates.CZ(0, 1),
        gates.H(1),
    ],
)
