# pylint: disable=union-attr
"""CircuitTranspiler class."""
from copy import deepcopy
from dataclasses import dataclass, field

from qililab.circuit import Circuit
from qililab.circuit.nodes.operation_node import OperationTiming
from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations import Barrier, PulseOperation, TranslatableToPulseOperation, Wait
from qililab.settings import RuncardSchema


@dataclass
class CircuitTranspiler:
    """CircuitTranspiler class."""

    circuit: Circuit
    settings: RuncardSchema.PlatformSettings
    circuit_ir1: Circuit | None = field(init=False, default=None)
    circuit_ir2: Circuit | None = field(init=False, default=None)

    def calculate_timings(self) -> Circuit:
        self.circuit_ir1 = deepcopy(self.circuit)
        nqubits = self.circuit_ir1.num_qubits
        layers = self.circuit_ir1.get_operation_layers(method=self.settings.timings_calculation_method)
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
        return self.circuit_ir1

    def translate_to_pulse_operations(self) -> Circuit:
        if self.circuit_ir1 is None:
            self.calculate_timings()
        self.circuit_ir2 = deepcopy(self.circuit_ir1)
        layers = self.circuit_ir2.get_operation_layers(method=self.settings.timings_calculation_method)  # type: ignore[union-attr]
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
        return self.circuit_ir2  # type: ignore[return-value]
