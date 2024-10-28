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

"""CircuitOptimizer class"""

from copy import deepcopy

from qibo import Circuit, gates


class CircuitOptimizer:
    """Optimizes a circuit, cancelling redundant gates."""

    @classmethod
    def run(cls, circuit):
        """Main method to run the circuit optimization with.

        Args:
            circuit (Circuit): circuit to optimize.

        Returns:
            Circuit: optimized circuit.
        """
        return cls.cancel_pairs_of_hermitian_gates(circuit)

    @classmethod
    def cancel_pairs_of_hermitian_gates(cls, circuit: Circuit) -> Circuit:
        """Optimizes circuit by cancelling adjacent hermitian gates.

        Args:
            circuit (Circuit): circuit to optimize.

        Returns:
            Circuit: optimized circuit.
        """
        # Initial and final circuit gates lists, from which to, one by one, after checks, pass non-cancelled gates:
        circ_list: list[tuple] = cls._get_circuit_gates(circuit)

        # We want to do the sweep circuit cancelling gates least once always:
        previous_circ_list = deepcopy(circ_list)
        output_circ_list = cls._sweep_circuit_cancelling_pairs_of_hermitian_gates(circ_list)

        # And then keep iterating, sweeping over the circuit (cancelling gates) each time, until there is full sweep without any cancellations:
        while output_circ_list != previous_circ_list:
            previous_circ_list = deepcopy(output_circ_list)
            output_circ_list = cls._sweep_circuit_cancelling_pairs_of_hermitian_gates(output_circ_list)

        # Create optimized circuit, from the obtained non-cancelled list:
        return cls._create_circuit(output_circ_list, circuit.nqubits)

    @staticmethod
    def _get_circuit_gates(circuit: Circuit) -> list[tuple]:
        """Get the gates of the circuit.

        Args:
            circuit (qibo.models.Circuit): Circuit to get the gates from.

        Returns:
            list[tuple]: List of gates in the circuit. Where each gate is a tuple (keys: 'name', value: 'qubits').
        """
        return [(type(gate).__name__, gate.qubits) for gate in circuit.queue]

    @staticmethod
    def _create_gate(gate_class: str, qubits: tuple[int]) -> gates.Gate:
        """Converts a tuple representation of qibo gate (name, qubits) into a Gate object.

        Args:
            gate_class (str): The class name of the gate. Can be "CNOT", "X", "H", or any Qibo supported class.
            qubits (tuple [int,] | tuple[int, int]): The qubits the gate acts on.

        Returns:
            gates.Gate: The qibo Gate object.
        """
        return getattr(gates, gate_class)(*qubits)

    @classmethod
    def _create_circuit(cls, gates_list: list[tuple], nqubits: int) -> Circuit:
        """Converts a list of gates (name, qubits) into a qibo Circuit object.

        Args:
            gates_list (list[tuple]): List of gates in the circuit. Where each gate is a tuple (keys: 'name', value: 'qubits').
            nqubits (int): Number of qubits in the circuit.

        Returns:
            Circuit: The qibo Circuit object.
        """
        # Create optimized circuit, from the obtained non-cancelled list:
        output_circuit = Circuit(nqubits)
        for gate, gate_qubits in gates_list:
            qibo_gate = cls._create_gate(gate, gate_qubits)
            output_circuit.add(qibo_gate)

        return output_circuit

    @staticmethod
    def _sweep_circuit_cancelling_pairs_of_hermitian_gates(circ_list: Circuit) -> Circuit:
        """Cancels adjacent gates in a circuit.

        Args:
            circ_list (list[tuple]): List of gates in the circuit. Where each gate is a tuple (keys: 'name', value: 'qubits').

        Returns:
            list[tuple]: List of gates in the circuit, after cancelling adjacent gates.
        """
        # List of gates, that are available for cancellation:
        hermitian_gates: list = ["H", "X", "Y", "Z", "CNOT", "CZ", "SWAP"]

        output_circ_list: list[tuple] = []

        while circ_list:  # If original circuit list, is empty or has one gate remaining, we are done:
            if len(circ_list) == 1:
                output_circ_list.append(circ_list[0])
                break

            # Gate of the original circuit, to find a match for:
            gate, gate_qubits = circ_list.pop(0)

            # If gate is not hermitian (can't be cancelled), add it to the output circuit and continue:
            if gate not in hermitian_gates:
                output_circ_list.append((gate, gate_qubits))
                continue

            subend = False
            for i in range(len(circ_list)):
                # Next gates, to compare the original with:
                comp_gate, comp_qubits = circ_list[i]

                # Simplify duplication, if same gate and qubits found, without any other in between:
                if gate == comp_gate and gate_qubits == comp_qubits:
                    circ_list.pop(i)
                    break

                # Add gate, if there is no other gate that acts on the same qubits:
                if i == len(circ_list) - 1:
                    output_circ_list.append((gate, gate_qubits))
                    break

                # Add gate and leave comparison_gate loop, if we find a gate in common qubit, that prevents contraction:
                for gate_qubit in gate_qubits:
                    if gate_qubit in comp_qubits:
                        output_circ_list.append((gate, gate_qubits))
                        subend = True
                        break
                if subend:
                    break

        return output_circ_list
