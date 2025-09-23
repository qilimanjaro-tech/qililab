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

"""This file contains the needed classes/methods to decompose gates into native"""

from collections.abc import Callable

import numpy as np
from qilisdk.digital import CNOT, CZ, RX, RY, RZ, SWAP, U1, U2, U3, Gate, H, I, M, S, T, X, Y, Z

from .native_gates import Drag


class GateDecompositions:
    """Abstract data structure that holds decompositions of"""

    def __init__(self):
        self.decompositions = {}

    def add(self, gate: type[Gate], decomposition: list[Gate] | Callable[[Gate], list[Gate]]):
        """Register a decomposition for a gate. Note that the decomposition list can have
        non-native gates

        Args:
            gate (Gate): gate to be decomposed
            decomposition (list(Gate)): list of gates for the decomposition

        """
        self.decompositions[gate] = decomposition

    def __call__(self, gate: Gate) -> list[Gate]:
        """Decompose a gate into native gates

        Args:
            gate (Gate): gate to decompose

        Returns:
            list[Gate]: list of gates corresponding to the decomposition of the given gate
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


def translate_gates(circuit_gates: list[Gate]) -> list[Gate]:
    """Maps QiliSDK gates to a hardware native implementation (CZ, RZ, Drag, Wait and M (Measurement))

    Check public docstring in :meth:`.CircuitTranspiler.gates_to_native()` for more information.

    Args:
        circuit_gates (list[Gate]): list of gates to be decomposed.

    Returns:
        list[Gate]: list of native gates corresponding to input gates
    """

    # define supported gates (native qpu gates + virtual z + measurement)
    supported_gates = (*native_gates(), RZ, M)

    # check which gates are native gates and if not all of them are so, translate
    to_translate = [not isinstance(gate, supported_gates) for gate in circuit_gates]
    new_gates = []

    # If no more gates to translate, finish:
    if sum(to_translate) == 0:
        return circuit_gates

    # iterate through all gates
    for gate, tt in zip(circuit_gates, to_translate):
        if not tt:
            new_gates.append(gate)  # append already native gates
        # distinguish 1 or 2 qubit gates
        else:
            new_gates += qili_dec(gate)
    return translate_gates(new_gates)


def native_gates():
    """List of native hardware gates

    Returns:
        tuple[Gate]: Hardware native gates
    """
    return (Drag, CZ)


# Mind that the order of the gates is "the inverse" of the operators
# i.e. to perform the operation AB|psi> the order of the operators
# returned as a list must be  [B, A] so that B is applied to |psi> 1st
qili_dec = GateDecompositions()
qili_dec.add(I, [RZ(0, phi=0)])
# qili_dec.add(Align, lambda gate: [Wait(0, gate.parameters[0])])
qili_dec.add(H, [Drag(0, theta=np.pi / 2, phase=-np.pi / 2), RZ(0, phi=np.pi)])
qili_dec.add(X, [Drag(0, theta=np.pi, phase=0)])
qili_dec.add(
    Y,
    [
        Drag(0, theta=np.pi, phase=0),
        RZ(0, phi=np.pi),
    ],
)
qili_dec.add(Z, [RZ(0, phi=np.pi)])

qili_dec.add(RX, lambda gate: [Drag(0, theta=gate.get_parameters()["theta"], phase=0)])
qili_dec.add(RY, lambda gate: [Drag(0, theta=gate.get_parameters()["theta"], phase=np.pi / 2)])
qili_dec.add(RZ, lambda gate: [RZ(0, phi=gate.get_parameters()["phi"] / 2)])
qili_dec.add(U1, lambda gate: [RZ(0, phi=gate.get_parameters()["phi"])])
qili_dec.add(
    U2, lambda gate: [U3(0, theta=np.pi / 2, phi=gate.get_parameters()["phi"], gamma=gate.get_parameters()["gamma"])]
)
qili_dec.add(
    U3,
    lambda gate: [
        Drag(
            0, theta=gate.get_parameters()["theta"], phase=-gate.get_parameters()["gamma"] + np.pi / 2
        ),  # qibo's U3 is different from standard U3
        RZ(0, phi=gate.get_parameters()["phi"] + gate.get_parameters()["gamma"]),
    ],
)
qili_dec.add(S, [RZ(0, phi=np.pi / 2)])
# qili_dec.add(SDG, [RZ(0, -np.pi / 2)])
qili_dec.add(T, [RZ(0, phi=np.pi / 4)])
# qili_dec.add(TDG, [RZ(0, -np.pi / 4)])

# register CZ decompositions
qili_dec.add(CNOT, [H(1), CZ(0, 1), H(1)])
qili_dec.add(CZ, [CZ(0, 1)])
qili_dec.add(
    SWAP,
    [
        H(1),
        CZ(0, 1),
        H(1),
        H(0),
        CZ(1, 0),
        H(0),
        H(1),
        CZ(0, 1),
        H(1),
    ],
)
# qili_dec.add(
#     iSWAP,
#     [
#         U3(0, np.pi / 2.0, 0, -np.pi / 2.0),
#         U3(1, np.pi / 2.0, 0, -np.pi / 2.0),
#         CZ(0, 1),
#         H(0),
#         H(1),
#         CZ(0, 1),
#         H(0),
#         H(1),
#     ],
# )
# qili_dec.add(
#     CRX,
#     lambda gate: [
#         RX(1, gate.parameters[0] / 2.0),
#         CZ(0, 1),
#         RX(1, -gate.parameters[0] / 2.0),
#         CZ(0, 1),
#     ],
# )
# qili_dec.add(
#     CRY,
#     lambda gate: [
#         RY(1, gate.parameters[0] / 2.0),
#         CZ(0, 1),
#         RY(1, -gate.parameters[0] / 2.0),
#         CZ(0, 1),
#     ],
# )
# qili_dec.add(
#     CRZ,
#     lambda gate: [
#         RZ(1, gate.parameters[0] / 2.0),
#         H(1),
#         CZ(0, 1),
#         RX(1, -gate.parameters[0] / 2.0),
#         CZ(0, 1),
#         H(1),
#     ],
# )
# qili_dec.add(
#     CU1,
#     lambda gate: [
#         RZ(0, gate.parameters[0] / 2.0),
#         H(1),
#         CZ(0, 1),
#         RX(1, -gate.parameters[0] / 2.0),
#         CZ(0, 1),
#         H(1),
#         RZ(1, gate.parameters[0] / 2.0),
#     ],
# )
# qili_dec.add(
#     CU2,
#     lambda gate: [
#         RZ(1, (gate.parameters[1] - gate.parameters[0]) / 2.0),
#         H(1),
#         CZ(0, 1),
#         H(1),
#         U3(1, -np.pi / 4, 0, -(gate.parameters[1] + gate.parameters[0]) / 2.0),
#         H(1),
#         CZ(0, 1),
#         H(1),
#         U3(1, np.pi / 4, gate.parameters[0], 0),
#     ],
# )
# qili_dec.add(
#     CU3,
#     lambda gate: [
#         RZ(1, (gate.parameters[2] - gate.parameters[1]) / 2.0),
#         H(1),
#         CZ(0, 1),
#         H(1),
#         U3(1, -gate.parameters[0] / 2.0, 0, -(gate.parameters[2] + gate.parameters[1]) / 2.0),
#         H(1),
#         CZ(0, 1),
#         H(1),
#         U3(1, gate.parameters[0] / 2.0, gate.parameters[1], 0),
#     ],
# )
# qili_dec.add(
#     FSWAP,
#     [
#         U3(0, np.pi / 2, -np.pi / 2, -np.pi),
#         U3(1, np.pi / 2, np.pi / 2, np.pi / 2),
#         CZ(0, 1),
#         U3(0, np.pi / 2, 0, -np.pi / 2),
#         U3(1, np.pi / 2, 0, np.pi / 2),
#         CZ(0, 1),
#         U3(0, np.pi / 2, np.pi / 2, -np.pi),
#         U3(1, np.pi / 2, 0, -np.pi),
#     ],
# )
# qili_dec.add(
#     RXX,
#     lambda gate: [
#         H(0),
#         CZ(0, 1),
#         RX(1, gate.parameters[0]),
#         CZ(0, 1),
#         H(0),
#     ],
# )
# qili_dec.add(
#     RYY,
#     lambda gate: [
#         RX(0, np.pi / 2),
#         U3(1, np.pi / 2, np.pi / 2, -np.pi),
#         CZ(0, 1),
#         RX(1, gate.parameters[0]),
#         CZ(0, 1),
#         RX(0, -np.pi / 2),
#         U3(1, np.pi / 2, 0, np.pi / 2),
#     ],
# )
# qili_dec.add(
#     RZZ,
#     lambda gate: [
#         H(1),
#         CZ(0, 1),
#         RX(1, gate.parameters[0]),
#         CZ(0, 1),
#         H(1),
#     ],
# )
# qili_dec.add(
#     TOFFOLI,
#     [
#         CZ(1, 2),
#         RX(2, -np.pi / 4),
#         CZ(0, 2),
#         RX(2, np.pi / 4),
#         CZ(1, 2),
#         RX(2, -np.pi / 4),
#         CZ(0, 2),
#         RX(2, np.pi / 4),
#         RZ(1, np.pi / 4),
#         H(1),
#         CZ(0, 1),
#         RZ(0, np.pi / 4),
#         RX(1, -np.pi / 4),
#         CZ(0, 1),
#         H(1),
#     ],
# )
