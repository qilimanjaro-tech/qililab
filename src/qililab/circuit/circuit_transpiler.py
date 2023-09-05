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

"""CircuitTranspiler class."""
from copy import deepcopy
from dataclasses import dataclass

from qililab.settings import Runcard
from qililab.typings.enums import ResetMethod

from .circuit import Circuit
from .nodes.operation_node import OperationTiming
from .operation_factory import OperationFactory
from .operations import Barrier, Measure, PulseOperation, Reset, SpecialOperation, TranslatableToPulseOperation, Wait


@dataclass
class CircuitTranspiler:
    """CircuitTranspiler class."""

    settings: Runcard.GatesSettings

    def calculate_timings(self, circuit: Circuit) -> Circuit:
        """Calculates the timings of all operations in a given quantum circuit and annotates the operation nodes with timing information.

        Args:
            circuit (Circuit): The quantum circuit for which timings need to be calculated.
        Returns:
            Circuit: The circuit with annotated operations that contain timing information.

        Raises:
            ValueError: If an unsupported operation is encountered in the circuit.
        """
        circuit = deepcopy(circuit)
        nqubits = circuit.num_qubits
        layers = circuit.get_operation_layers(method=self.settings.timings_calculation_method)
        qubits_last_end_timings = [0 for _ in range(nqubits)]
        for index, layer in enumerate(layers):
            # Calculate maximum end time of previous layer
            max_end_time_of_previous_layer = (
                max(op_node.timing.end for op_node in layers[index - 1] if op_node.timing is not None)
                if index >= 1
                else 0
            )
            for operation_node in layer:
                # Initial guess of start time of operation
                start_time = max(
                    [qubits_last_end_timings[qubit] for qubit in operation_node.qubits]
                    + [max_end_time_of_previous_layer]
                )
                # Calculate [start-end] time of operation
                if isinstance(operation_node.operation, TranslatableToPulseOperation):
                    operation_settings = self.settings.get_operation_settings(operation_node.operation.name.value)
                    pulse_duration = operation_settings.pulse.duration
                    delay = (
                        self.settings.delay_before_readout
                        if isinstance(operation_node.operation, Measure)
                        else self.settings.delay_between_pulses
                    )
                    start_time = start_time + delay
                    end_time = start_time + pulse_duration
                elif isinstance(operation_node.operation, PulseOperation):
                    start_time = start_time + self.settings.delay_between_pulses
                    end_time = start_time + operation_node.operation.duration
                elif isinstance(operation_node.operation, Wait):
                    end_time = start_time + operation_node.operation.t
                elif isinstance(operation_node.operation, Barrier):
                    end_time = start_time
                elif isinstance(operation_node.operation, Reset):
                    if self.settings.reset_method == ResetMethod.PASSIVE:
                        end_time = start_time + self.settings.passive_reset_duration
                else:
                    raise ValueError(f"Operation {operation_node} not supported for translation yet.")
                # Update timings
                operation_node.timing = OperationTiming(start=start_time, end=end_time)
                for qubit in operation_node.qubits:
                    qubits_last_end_timings[qubit] = end_time
        circuit.has_timings_calculated = True
        return circuit

    def remove_special_operations(self, circuit: Circuit) -> Circuit:
        """Removes special operations (Wait, Barrier, Passive Reset) from the circuit

        Args:
            circuit (Circuit): The quantum circuit

        Returns:
            Circuit: New circuit with special operations removed
        """
        circuit = deepcopy(circuit)
        if not circuit.has_timings_calculated:
            circuit = self.calculate_timings(circuit)
        layers = circuit.get_operation_layers(method=self.settings.timings_calculation_method)
        for layer in layers:  # pylint: disable=too-many-nested-blocks
            for operation_node in layer:
                if isinstance(operation_node.operation, SpecialOperation):
                    predecessors = circuit.graph.predecessors(operation_node.index)
                    successors = circuit.graph.successors(operation_node.index)
                    for predecessor in predecessors:
                        for successor in successors:
                            predecessor_qubits = set(predecessor.qubits)
                            successor_qubits = set(successor.qubits)
                            node_qubits = set(operation_node.qubits)
                            if predecessor_qubits & successor_qubits & node_qubits:
                                circuit.graph.add_edge(predecessor.index, successor.index, None)
                    circuit.graph.remove_node(operation_node.index)
        circuit.has_special_operations_removed = True
        return circuit

    def transpile_to_pulse_operations(self, circuit: Circuit) -> Circuit:
        """
        Transpiles the given quantum circuit into pulse operations.

        Args:
            circuit (Circuit): The quantum circuit to be transpiled into pulse operations.

        Returns:
            Circuit: The transpiled circuit with pulse operations.
        """
        circuit = deepcopy(circuit)
        if not circuit.has_timings_calculated:
            circuit = self.calculate_timings(circuit)
        if not circuit.has_special_operations_removed:
            circuit = self.remove_special_operations(circuit)
        layers = circuit.get_operation_layers(method=self.settings.timings_calculation_method)
        for layer in layers:
            for operation_node in layer:
                if isinstance(operation_node.operation, TranslatableToPulseOperation):
                    operation_settings = self.settings.get_operation_settings(operation_node.operation.name.value)
                    pulse_operation_settings = operation_settings.pulse
                    pulse_operation_name = pulse_operation_settings.name
                    pulse_operation_parameters = {
                        "amplitude": pulse_operation_settings.amplitude,
                        "duration": pulse_operation_settings.duration,
                        **pulse_operation_settings.parameters,
                    }
                    pulse_operation = OperationFactory.get(pulse_operation_name)(**pulse_operation_parameters)
                    operation_node.operation = pulse_operation
        circuit.has_transpiled_to_pulses = True
        return circuit
