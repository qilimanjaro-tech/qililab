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

"""File containing the supported native gates."""

import numpy as np
from qibo import Circuit, gates
from qibo.gates.abstract import Gate, ParametrizedGate
from qibo.gates.gates import _Un_

from qililab import digital


class Drag(_Un_):
    r"""Native drag pulse dummy class.
    Inherits from qibo unitary gates class

    The native gate is a drag pulse
    .. math::

        R_{MW}(\theta, \phi) = Z_\phi X_\theta Z_{-\phi}

    Please note that the negative Z rotations is applied first! The circuit drawing of this gate looks like the
    following:

    .. math::

        --|RZ(-phi)|--|RX(theta)|--|RZ(phi)|--

    Together with virtual Z gates, this allows us to perform any single-qubit gate, since any
    such gate can be expressed as a unitary
    .. math::

        U(\theta,\phi,\lambda) = Z_\phi X_\theta Z_\lambda &= R_{MW}(\theta, \phi)Z_{\lambda+\phi} &=
        Z_{\phi+\lambda}R_{MW}(\theta, -\lambda)

    Args:
        q (int): qubit where the gate is applied
        theta (float): theta angle of rotation in radians
        phase (float): phase of  the Drag pulse
        trainable (bool): whether parameters are trainable (set to false)
    """

    def __init__(self, q: int, theta: float, phase: float, trainable: bool = True):
        super().__init__(q, trainable=trainable)
        self.name = "drag"
        self.nparams = 2
        self.init_kwargs = {"theta": theta, "phase": phase, "trainable": trainable}
        self.parameter_names = ["theta", "phase"]
        self.parameters = theta, phase

    @property
    def raw(self) -> dict:
        """Serialize to dictionary.

        The values used in the serialization should be compatible with a
        JSON dump (or any other one supporting a minimal set of scalar
        types). Though the specific implementation is up to the specific
        gate.
        """
        encoded_simple = super().raw
        encoded_simple["init_kwargs"] = self.init_kwargs
        return encoded_simple


class Wait(ParametrizedGate):
    """The Wait gate.

    Args:
        q (int): the qubit index.
        t (int): the time to wait (ns)
    """

    def __init__(self, q, t):
        super().__init__(trainable=True)
        self.name = "wait"
        self._controlled_gate = None
        self.target_qubits = (q,)

        self.parameters = t
        self.init_args = [q]
        self.init_kwargs = {"t": t}

    @property
    def raw(self) -> dict:
        """Serialize to dictionary.

        The values used in the serialization should be compatible with a
        JSON dump (or any other one supporting a minimal set of scalar
        types). Though the specific implementation is up to the specific
        gate.
        """
        encoded_simple = super().raw
        encoded_simple["init_kwargs"] = self.init_kwargs
        return encoded_simple


class _GateHandler:
    """Class to handle the native gates of the Qibo circuit."""

    @staticmethod
    def normalize_angle(angle: float):
        """Normalizes angle in range [-pi, pi].

        Args:
            angle (float): Normalized angle.
        """
        angle %= 2 * np.pi
        if angle > np.pi:
            angle -= 2 * np.pi
        return angle

    @staticmethod
    def get_circuit_gates_info(circuit_gates: list[gates.Gate]) -> list[dict]:
        """Get the gates of the circuit.

        Args:
            circuit_gates (list[gates.Gate]): list of native gates of the Qibo circuit.

        Returns:
            list[dict]: List of gates information in the circuit. Where each element is the qibo raw info of the gate.
        """
        return [gate.raw for gate in circuit_gates]

    @staticmethod
    def create_gate(gate_info: dict) -> gates.Gate:
        """Converts a tuple representation of qibo gate (name, qubits) into a Gate object.

        Args:
            gate_info (dict): List of gates information in the circuit. Where each element is the qibo raw info of the gate.

        Returns:
            gates.Gate: The qibo Gate object.
        """
        # Solve Identity gate, argument int issue:
        if gate_info["_class"] in {"Drag", "Wait"}:
            return getattr(digital, gate_info["_class"])(*gate_info["init_args"], **gate_info["init_kwargs"])
        return Gate.from_dict(gate_info)

    @staticmethod
    def create_qibo_gates_from_gates_info(circuit_gates: list[dict]) -> list[gates.Gate]:
        """Converts a list of gate info (name, qubits) into a list of Qibo gates.

        Args:
            circuit_gates (list[tuple]): List of information of each gate in the circuit, after cancelling adjacent gates. Where each element is the qibo raw info of the gate.
            nqubits (int): Number of qubits in the circuit.

        Returns:
            list[gates.Gate]: Gate list of the qibo Circuit.
        """
        # Create optimized circuit, from the obtained non-cancelled list:
        output_gates = []
        for gate_info in circuit_gates:
            qibo_gate = _GateHandler.create_gate(gate_info)
            output_gates.append(qibo_gate)

        return output_gates

    @staticmethod
    def create_circuit_from_gates(queue: list[gates.Gate], nqubits: int, wire_names: list[int] | None) -> Circuit:
        """
        Creates a quantum circuit from a list of gate operations.

        Args:
            queue (list[gates.Gate]): A list of gate operations to be added to the circuit.
            nqubits (int): The number of qubits in the circuit.
            wire_names (list[int], optional): Wire names of the circuit to create.

        Returns:
            Circuit: The constructed quantum circuit with the specified gates and number of qubits.
        """
        optimized_circuit = Circuit(nqubits)
        optimized_circuit.add(queue)
        optimized_circuit.wire_names = wire_names

        return optimized_circuit
