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

"""QiliQasmConvert

This file provides the `QiliQasmConverter` class, which is responsible for converting Qililab quantum circuits
to and from QILIQASM format. The QILIQASM format is a custom representation designed specifically for Qililab circuits.
"""
from qililab.circuit import Circuit  # pylint: disable=cyclic-import
from qililab.circuit.operations import Operation  # pylint: disable=cyclic-import
from qililab.config.version import __version__


class QiliQasmConverter:
    """
    A utility class for converting Qililab quantum circuits to and from QILIQASM format.
    """

    @staticmethod
    def to_qasm(circuit: Circuit):
        """
        Convert a Qililab quantum circuit to QILIQASM format.

        Args:
            circuit (Circuit): The Qililab quantum circuit to convert.

        Returns:
            str: The QILIQASM representation of the given quantum circuit.
        """
        code = [f"// Generated by Qililab {__version__}"]
        code += ["// QILIQASM 1.0"]
        code += [f"Circuit {circuit.num_qubits}"]

        layers = circuit.get_operation_layers()
        for layer in layers:
            for operation_node in layer:
                qubits = ",".join(f"{qubit}" for qubit in operation_node.qubits)
                operation = str(operation_node.operation)
                code += [f"{qubits} {operation}"]

        return "\n".join(code)

    @staticmethod
    def from_qasm(qasm: str):
        """
        Convert a QILIQASM string to a Qililab quantum circuit.

        Args:
            qasm (str): The QILIQASM representation of a quantum circuit.

        Returns:
            Circuit: The Qililab quantum circuit created from the QILIQASM string.
        """
        lines = qasm.split("\n")
        for line in lines:
            if line.startswith("//"):
                continue
            first_str, second_str = line.split(None, 1)
            if first_str == "Circuit":
                num_qubits = int(second_str)
                circuit = Circuit(num_qubits)
            else:
                qubits = tuple(int(qubit) for qubit in first_str.split(","))
                operation = Operation.parse(second_str)
                circuit.add(qubits, operation)
        return circuit
