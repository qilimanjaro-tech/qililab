"""ExecutionManager class."""
from dataclasses import dataclass
from re import I
from typing import Tuple, Type

import rustworkx as rx

from qililab.circuit import Circuit
from qililab.circuit.nodes import OperationNode
from qililab.circuit.nodes.operation_node import OperationTiming
from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations import (
    R180,
    Barrier,
    Measure,
    Operation,
    PulseOperation,
    Rxy,
    TranslatableToPulseOperation,
    Wait,
    X,
)
from qililab.settings import RuncardSchema


@dataclass
class CircuitTranspiler:
    """CircuitTranspiler class."""

    circuit: Circuit
    settings: RuncardSchema.PlatformSettings

    def calculate_timings(self) -> None:
        nqubits = self.circuit.num_qubits
        layers = self.circuit.get_operation_layers(method=self.settings.timings_calculation_method)
        qubits_last_end_timings = [0 for _ in range(nqubits)]
        for index, layer in enumerate(layers):
            for operation_node in layer:
                max_end_time_of_previous_layer = (
                    max([op_node.timing.end for op_node in layers[index - 1] if op_node.timing is not None])
                    if index >= 1
                    else 0
                )
                if isinstance(operation_node.operation, TranslatableToPulseOperation):
                    operation_settings = self.settings.get_operation_settings(operation_node.operation.name.value)
                    pulse_duration = (
                        operation_settings.pulse.duration
                        if isinstance(operation_settings.pulse.duration, int)
                        else operation_settings.pulse.duration.value
                    )
                    start_time = (
                        max(
                            [qubits_last_end_timings[qubit] for qubit in operation_node.qubits]
                            + [max_end_time_of_previous_layer]
                        )
                        + self.settings.delay_between_pulses
                    )
                    end_time = start_time + pulse_duration
                    operation_node.timing = OperationTiming(start=start_time, end=end_time)
                    for qubit in operation_node.qubits:
                        qubits_last_end_timings[qubit] = end_time
                elif isinstance(operation_node.operation, PulseOperation):
                    start_time = (
                        max(
                            [qubits_last_end_timings[qubit] for qubit in operation_node.qubits]
                            + [max_end_time_of_previous_layer]
                        )
                        + self.settings.delay_between_pulses
                    )
                    end_time = start_time + operation_node.operation.duration
                    operation_node.timing = OperationTiming(start=start_time, end=end_time)
                    for qubit in operation_node.qubits:
                        qubits_last_end_timings[qubit] = end_time
                elif isinstance(operation_node.operation, Wait):
                    start_time = max(
                        [qubits_last_end_timings[qubit] for qubit in operation_node.qubits]
                        + [max_end_time_of_previous_layer]
                    )
                    end_time = start_time + operation_node.operation.t
                    operation_node.timing = OperationTiming(start=start_time, end=end_time)
                    for qubit in operation_node.qubits:
                        qubits_last_end_timings[qubit] = end_time
                elif isinstance(operation_node.operation, Barrier):
                    start_time = max(
                        [qubits_last_end_timings[qubit] for qubit in operation_node.qubits]
                        + [max_end_time_of_previous_layer]
                    )
                    end_time = start_time
                    operation_node.timing = OperationTiming(start=start_time, end=end_time)
                    for qubit in operation_node.qubits:
                        qubits_last_end_timings[qubit] = end_time
                else:
                    raise ValueError(f"Operation {operation_node} not supported for translation yet.")

    def translate_to_pulse_operations(self):
        layers = self.circuit.get_operation_layers(method=self.settings.timings_calculation_method)
        for index, layer in enumerate(layers):
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
