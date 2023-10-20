import hashlib
import math
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import qm.qua as qua
from qm.qua import _dsl as qua_dsl
from qualang_tools.config.integration_weights_tools import convert_integration_weights

from qililab.qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qililab.qprogram.blocks.infinite_loop import InfiniteLoop
from qililab.qprogram.operations import (
    Acquire,
    Measure,
    Operation,
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.variable import Domain, Variable
from qililab.waveforms import IQPair, Square, Waveform


class BusCompilationInfo:
    def __init__(self):
        self.current_gain: float | qua.QuaVariableType | None = None


class MeasurementInfo:
    def __init__(
        self,
        variable_I: qua.QuaVariableType | None = None,
        variable_Q: qua.QuaVariableType | None = None,
        stream_I: qua_dsl._ResultSource | None = None,
        stream_Q: qua_dsl._ResultSource | None = None,
        stream_raw_adc: qua_dsl._ResultSource | None = None,
    ):
        self.variable_I: qua.QuaVariableType | None = variable_I
        self.variable_Q: qua.QuaVariableType | None = variable_Q
        self.stream_I: qua_dsl._ResultSource | None = stream_I
        self.stream_Q: qua_dsl._ResultSource | None = stream_Q
        self.stream_raw_adc: qua_dsl._ResultSource | None = stream_raw_adc
        self.loops_iterations: list[int] = []
        self.stream_processing_pending: bool = True


class AveragingInfo:
    def __init__(self, shots: int, variable: qua.QuaVariableType, stream: qua_dsl._ResultSource):
        self.shots: int = shots
        self.variable: qua.QuaVariableType = variable
        self.stream: qua_dsl._ResultSource = stream
        self.save_pending: bool = True
        self.stream_processing_pending: bool = True


class QuantumMachinesCompiler:
    """_summary_"""

    def __init__(self):
        # Handlers to map each operation to a corresponding handler function
        self._handlers: dict[type, Callable] = {
            InfiniteLoop: self._handle_infinite_loop,
            ForLoop: self._handle_for_loop,
            Loop: self._handle_loop,
            Average: self._handle_average,
            Measure: self._handle_measure,
            Play: self._handle_play,
            SetFrequency: self._handle_set_frequency,
            SetPhase: self._handle_set_phase,
            SetGain: self._handle_set_gain,
            ResetPhase: self._handle_reset_phase,
            Wait: self._handle_wait,
            Sync: self._handle_sync,
        }

        self._qprogram: QProgram
        self._bus_mappings: dict[str, str] | None
        self._qprogram_block_stack: deque[Block]
        self._qprogram_to_qua_variables: dict[Variable, qua.QuaVariableType]
        self._measurements: list[MeasurementInfo]
        self._averages: list[AveragingInfo]
        self._configuration: dict
        self._buses: dict[str, BusCompilationInfo]

    def compile(
        self, qprogram: QProgram, bus_mappings: dict[str, str] | None = None
    ) -> tuple[qua.Program, dict, list[str]]:
        """Compile QProgram to QUA's Program.

        Args:
            qprogram (QProgram): The QProgram to be compiled

        Returns:
            qua.Program: The compiled program.
        """

        def traverse(block: Block):
            self._qprogram_block_stack.append(block)
            for element in block.elements:
                handler = self._handlers.get(type(element))
                if not handler:
                    raise NotImplementedError(
                        f"{element.__class__} operation is currently not supported in Quantum Machines."
                    )
                if isinstance(element, (InfiniteLoop, ForLoop, Loop, Average, Parallel)):
                    with handler(element):
                        traverse(element)
                        if isinstance(element, Average):
                            self._save_average()
                elif isinstance(element, Block):
                    traverse(element)
                else:
                    handler(element)
            self._qprogram_block_stack.pop()

        self._qprogram = qprogram
        self._bus_mappings = bus_mappings

        self._qprogram_block_stack = deque()
        self._qprogram_to_qua_variables = {}
        self._measurements = []
        self._averages = []
        self._configuration = {
            "waveforms": {},
            "pulses": {},
            "integration_weights": {},
            "digital_waveforms": {"ON": {"samples": [(1, 0)]}, "OFF": {"samples": [(0, 0)]}},
            "elements": {},
        }

        self._populate_buses()

        with qua.program() as qua_program:
            # Declare variables
            self._declare_variables()
            # Recursive traversal to convert QProgram blocks to Sequence
            traverse(self._qprogram._program)
            # Stream Processing
            with qua.stream_processing():
                result_handles = self._process_streams()

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        return qua_program, self._configuration, result_handles

    def _save_average(self):
        average = next(average for average in self._averages if average.save_pending)
        average.save_pending = False
        qua.save(average.variable, average.stream)

    def _process_streams(self):
        result_handles: list[str] = []

        measurements = [measurement for measurement in self._measurements if measurement.stream_processing_pending]
        if len(measurements) == 1:
            measurement = measurements[0]
            if measurement.stream_I is not None:
                for loop_iteration in measurement.loops_iterations:
                    measurement.stream_I = measurement.stream_I.buffer(loop_iteration)
                measurement.stream_I = measurement.stream_I.average()
                measurement.stream_I.save_all("I")
                result_handles.append("I")
            if measurement.stream_Q is not None:
                for loop_iteration in measurement.loops_iterations:
                    measurement.stream_Q = measurement.stream_Q.buffer(loop_iteration)
                measurement.stream_Q = measurement.stream_Q.average()
                measurement.stream_Q.save_all("Q")
                result_handles.append("Q")
            if measurement.stream_raw_adc is not None:
                measurement.stream_raw_adc.input1().average().save_all("adc1")
                measurement.stream_raw_adc.input2().average().save_all("adc2")
                result_handles.append("adc1")
                result_handles.append("adc2")

        averages = [average for average in self._averages if average.stream_processing_pending]
        if len(averages) == 1:
            average = averages[0]
            average.stream.save_all("iteration")

        return result_handles

    def _declare_variables(self):
        for variable in self._qprogram._variables:
            if variable.domain in [Domain.Time, Domain.Frequency]:
                qua_variable = qua.declare(int)
            else:
                qua_variable = qua.declare(qua.fixed)
            self._qprogram_to_qua_variables[variable] = qua_variable

    def _populate_buses(self):
        """Map each bus in the QProgram to a BusCompilationInfo instance.

        Returns:
            A dictionary where the keys are bus names and the values are BusCompilationInfo objects.
        """

        def collect_buses(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_buses(element)
                if isinstance(element, Operation):
                    bus = getattr(element, "bus", None)
                    if bus:
                        yield self._bus_mappings[bus] if self._bus_mappings and bus in self._bus_mappings else bus

        buses = set(collect_buses(self._qprogram._program))
        self._configuration["elements"] = {bus: {"operations": {}} for bus in buses}
        self._buses = {bus: BusCompilationInfo() for bus in buses}

    def _handle_infinite_loop(self, _: InfiniteLoop):
        return qua.infinite_loop_()

    def _handle_for_loop(self, element: ForLoop):
        qua_variable = self._qprogram_to_qua_variables[element.variable]
        start, stop, step = element.start, element.stop, element.step
        if element.variable.domain is Domain.Phase:
            start, stop, step = start / 360.0, stop / 360.0, step / 360.0
        if element.variable.domain is Domain.Frequency:
            start, stop, step = int(start * 1e3), int(stop * 1e3), int(step * 1e3)
        if element.variable.domain is Domain.Time:
            start, stop, step = max(start, 4), stop, step
        to_positive = stop >= start
        if to_positive:
            return qua.for_(qua_variable, start, qua_variable <= stop, qua_variable + step)
        else:
            return qua.for_(qua_variable, start, qua_variable >= stop, qua_variable + step)

    def _handle_loop(self, element: Loop):
        qua_variable = self._qprogram_to_qua_variables[element.variable]
        values = element.values
        if element.variable.domain is Domain.Phase:
            values = values / 360.0
        if element.variable.domain is Domain.Frequency:
            values = (values * 1e3).astype(int)
        return qua.for_each_(qua_variable, values)

    def _handle_average(self, element: Average):
        variable = qua.declare(int)
        stream = qua.declare_stream()
        self._averages.append(AveragingInfo(shots=element.shots, variable=variable, stream=stream))
        return qua.for_(variable, 0, variable < element.shots, variable + 1)

    def _handle_set_frequency(self, element: SetFrequency):
        bus = (
            self._bus_mappings[element.bus] if self._bus_mappings and element.bus in self._bus_mappings else element.bus
        )
        frequency = (
            self._qprogram_to_qua_variables[element.frequency]
            if isinstance(element.frequency, Variable)
            else element.frequency * 1e3
        )
        qua.update_frequency(element=bus, new_frequency=frequency, units="mHz")

    def _handle_set_phase(self, element: SetPhase):
        bus = (
            self._bus_mappings[element.bus] if self._bus_mappings and element.bus in self._bus_mappings else element.bus
        )
        phase = (
            self._qprogram_to_qua_variables[element.phase]
            if isinstance(element.phase, Variable)
            else element.phase / 360.0
        )
        qua.frame_rotation_2pi(phase, bus)

    def _handle_reset_phase(self, element: ResetPhase):
        bus = (
            self._bus_mappings[element.bus] if self._bus_mappings and element.bus in self._bus_mappings else element.bus
        )
        qua.reset_frame(bus)

    def _handle_set_gain(self, element: SetGain):
        bus = (
            self._bus_mappings[element.bus] if self._bus_mappings and element.bus in self._bus_mappings else element.bus
        )
        gain = self._qprogram_to_qua_variables[element.gain] if isinstance(element.gain, Variable) else element.gain
        # QUA doesn't have a method for setting the gain directly.
        # Instead, it uses an amplitude multiplication with `amp()`.
        # Thus, we store the current gain to multiply with in the next play instructions.
        self._buses[bus].current_gain = gain

    def _handle_play(self, element: Play):
        bus = (
            self._bus_mappings[element.bus] if self._bus_mappings and element.bus in self._bus_mappings else element.bus
        )
        waveform_I, waveform_Q = element.get_waveforms()
        waveform_variables = element.get_waveform_variables()
        duration = waveform_I.get_duration()
        if waveform_Q and duration != waveform_Q.get_duration():
            raise ValueError()
        if not waveform_variables:
            waveform_I_name = self.__add_waveform_to_configuration(waveform_I)
            waveform_Q_name = self.__add_waveform_to_configuration(waveform_Q) if waveform_Q else None
            pulse_name = self.__add_or_update_control_pulse_to_configuration(waveform_I_name, waveform_Q_name, duration)
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = (
                operation_name * qua.amp(self._buses[bus].current_gain)
                if self._buses[bus].current_gain is not None
                else operation_name
            )
            qua.play(pulse, bus)

    def _handle_measure(self, element: Measure):
        bus = (
            self._bus_mappings[element.bus] if self._bus_mappings and element.bus in self._bus_mappings else element.bus
        )
        waveform_I, waveform_Q = element.get_waveforms()
        if (measurement_duration := waveform_I.get_duration()) != waveform_Q.get_duration():
            raise ValueError()

        waveform_I_name = self.__add_waveform_to_configuration(waveform_I)
        waveform_Q_name = self.__add_waveform_to_configuration(waveform_Q)

        variable_I, variable_Q, stream_I, stream_Q, stream_raw_adc = None, None, None, None, None

        if element.save_raw_adc:
            stream_raw_adc = qua.declare_stream(adc_trace=True)

        if element.weights is None:
            pulse_name = self.__add_or_update_measurement_pulse_to_configuration(
                waveform_I_name, waveform_Q_name, duration=measurement_duration, integration_weights=[]
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = (
                operation_name * qua.amp(self._buses[bus].current_gain)
                if self._buses[bus].current_gain is not None
                else operation_name
            )
            qua.measure(pulse, element.bus, stream_raw_adc)
        elif isinstance(element.weights, IQPair):
            variable_I = qua.declare(qua.fixed)
            stream_I = qua.declare_stream()
            weight_I = self.__add_integration_weight_to_configuration(element.weights.I, element.weights.Q)
            pulse_name = self.__add_or_update_measurement_pulse_to_configuration(
                waveform_I_name, waveform_Q_name, duration=measurement_duration, integration_weights=[weight_I]
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = (
                operation_name * qua.amp(self._buses[bus].current_gain)
                if self._buses[bus].current_gain is not None
                else operation_name
            )
            if element.demodulation:
                qua.measure(pulse, bus, stream_raw_adc, qua.demod.full(weight_I, variable_I))
            else:
                qua.measure(pulse, bus, stream_raw_adc, qua.integration.full(weight_I, variable_I))
            qua.save(variable_I, stream_I)
        elif isinstance(element.weights, tuple) and len(element.weights) == 2:
            variable_I = qua.declare(qua.fixed)
            variable_Q = qua.declare(qua.fixed)
            stream_I = qua.declare_stream()
            stream_Q = qua.declare_stream()
            weight_I = self.__add_integration_weight_to_configuration(element.weights[0].I, element.weights[0].Q)
            weight_Q = self.__add_integration_weight_to_configuration(element.weights[1].I, element.weights[1].Q)
            pulse_name = self.__add_or_update_measurement_pulse_to_configuration(
                waveform_I_name,
                waveform_Q_name,
                duration=measurement_duration,
                integration_weights=[weight_I, weight_Q],
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = (
                operation_name * qua.amp(self._buses[bus].current_gain)
                if self._buses[bus].current_gain is not None
                else operation_name
            )
            if element.demodulation:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.demod.full(weight_I, variable_I),
                    qua.demod.full(weight_Q, variable_Q),
                )
            else:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.integration.full(weight_I, variable_I),
                    qua.integration.full(weight_Q, variable_Q),
                )
            qua.save(variable_I, stream_I)
            qua.save(variable_Q, stream_Q)
        elif isinstance(element.weights, tuple) and len(element.weights) == 3:
            variable_I = qua.declare(qua.fixed)
            variable_Q = qua.declare(qua.fixed)
            stream_I = qua.declare_stream()
            stream_Q = qua.declare_stream()
            weight_A = self.__add_integration_weight_to_configuration(element.weights[0].I, element.weights[0].Q)
            weight_B = self.__add_integration_weight_to_configuration(element.weights[1].I, element.weights[1].Q)
            weight_C = self.__add_integration_weight_to_configuration(element.weights[2].I, element.weights[2].Q)  # type: ignore[misc]
            pulse_name = self.__add_or_update_measurement_pulse_to_configuration(
                waveform_I_name,
                waveform_Q_name,
                duration=measurement_duration,
                integration_weights=[weight_A, weight_B, weight_C],
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = (
                operation_name * qua.amp(self._buses[bus].current_gain)
                if self._buses[bus].current_gain is not None
                else operation_name
            )
            if element.demodulation:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.dual_demod.full(weight_A, "out1", weight_B, "out2", variable_I),
                    qua.dual_demod.full(weight_C, "out1", weight_A, "out2", variable_Q),
                )
            else:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.dual_integration.full(weight_A, "out1", weight_B, "out2", variable_I),
                    qua.dual_demod.full(weight_C, "out1", weight_A, "out2", variable_Q),
                )
            qua.save(variable_I, stream_I)
            qua.save(variable_Q, stream_Q)

        measurement_info = MeasurementInfo(variable_I, variable_Q, stream_I, stream_Q, stream_raw_adc)
        for block in reversed(self._qprogram_block_stack):
            if isinstance(block, ForLoop):
                iterations = QuantumMachinesCompiler.__calculate_iterations(block.start, block.stop, block.step)
                measurement_info.loops_iterations.append(iterations)
            if isinstance(block, Loop):
                iterations = len(block.elements)
                measurement_info.loops_iterations.append(iterations)

        self._measurements.append(measurement_info)

    def _handle_wait(self, element: Wait):
        bus = (
            self._bus_mappings[element.bus] if self._bus_mappings and element.bus in self._bus_mappings else element.bus
        )
        duration = (
            self._qprogram_to_qua_variables[element.duration]
            if isinstance(element.duration, Variable)
            else max(element.duration, 4)
        )
        qua.wait(duration, bus)

    def _handle_sync(self, element: Sync):
        if element.buses:
            buses = [
                self._bus_mappings[bus] if self._bus_mappings and bus in self._bus_mappings else bus
                for bus in element.buses
            ]
            qua.align(*buses)
        else:
            qua.align()

    def __add_pulse_to_element_operations(self, element: str, pulse: str):
        if pulse not in self._configuration["elements"][element]["operations"]:
            self._configuration["elements"][element]["operations"][pulse] = pulse
        return pulse

    def __add_or_update_control_pulse_to_configuration(
        self, waveform_I_name: str, waveform_Q_name: str | None, duration: int
    ):
        pulse_name = (
            f"control_{waveform_I_name}_{waveform_Q_name}_{duration}"
            if waveform_Q_name
            else f"control_{waveform_I_name}_{duration}"
        )
        if pulse_name not in self._configuration["pulses"]:
            configuration = {
                "operation": "control",
                "length": duration,
                "waveforms": {"I": waveform_I_name, "Q": waveform_Q_name}
                if waveform_Q_name
                else {"single": waveform_I_name},
            }
            self._configuration["pulses"][pulse_name] = configuration
        return pulse_name

    def __add_or_update_measurement_pulse_to_configuration(
        self, waveform_I_name: str, waveform_Q_name: str, duration: int, integration_weights: list[str]
    ):
        pulse_name = f"measurement_{waveform_I_name}_{waveform_Q_name}_{duration}"
        if pulse_name not in self._configuration["pulses"]:
            self._configuration["pulses"][pulse_name] = {
                "operation": "measurement",
                "length": duration,
                "waveforms": {
                    "I": waveform_I_name,
                    "Q": waveform_Q_name,
                },
                "integration_weights": {weight: weight for weight in integration_weights},
                "digital_marker": "ON",
            }
        else:
            self._configuration["pulses"][pulse_name]["integration_weights"].update(integration_weights)
        return pulse_name

    def __add_integration_weight_to_configuration(self, cosine_part: Waveform, sine_part: Waveform):
        weight_name = f"{QuantumMachinesCompiler.__hash_waveform(cosine_part)}_{QuantumMachinesCompiler.__hash_waveform(sine_part)}"
        if weight_name not in self._configuration["integration_weights"]:
            self._configuration["integration_weights"][
                weight_name
            ] = QuantumMachinesCompiler.__integration_weight_to_config(cosine_part, sine_part)
        return weight_name

    def __add_waveform_to_configuration(self, waveform: Waveform):
        waveform_name = QuantumMachinesCompiler.__hash_waveform(waveform)
        if waveform_name not in self._configuration["waveforms"]:
            self._configuration["waveforms"][waveform_name] = QuantumMachinesCompiler.__waveform_to_config(waveform)
        return waveform_name

    @staticmethod
    def __hash_waveform(waveform: Waveform):
        attributes = [
            f"{key}: {(QuantumMachinesCompiler.__hash_waveform(value) if isinstance(value, Waveform) else str(value))}"
            for key, value in waveform.__dict__.items()
            if key != "duration"
        ]
        string_to_hash = f"{waveform.__class__.__name__}({','.join(attributes)})"
        hash_result = hashlib.md5(string_to_hash.encode("utf-8"), usedforsecurity=False)
        return hash_result.hexdigest()[:8]

    @staticmethod
    def __waveform_to_config(waveform: Waveform):
        if isinstance(waveform, Square):
            return {"type": "constant", "sample": waveform.amplitude}
        else:
            return {"type": "arbitrary", "samples": waveform.envelope().tolist()}

    @staticmethod
    def __integration_weight_to_config(cosine_part: Waveform, sine_part: Waveform):
        cosine_envelope, sine_envelope = cosine_part.envelope(resolution=4), sine_part.envelope(resolution=4)
        converted_cosine_part = convert_integration_weights(integration_weights=cosine_envelope, N=len(cosine_envelope))
        converted_sine_part = convert_integration_weights(integration_weights=sine_envelope, N=len(sine_envelope))

        return {"cosine": converted_cosine_part, "sine": converted_sine_part}

    @staticmethod
    def __calculate_iterations(start: int | float, stop: int | float, step: int | float):
        if step == 0:
            raise ValueError("Step value cannot be zero")

        # Calculate the raw number of iterations
        raw_iterations = (stop - start + step) / step

        # If the raw number of iterations is very close to an integer, round it to that integer
        # This accounts for potential floating-point inaccuracies
        if abs(raw_iterations - round(raw_iterations)) < 1e-9:
            return round(raw_iterations)
        else:
            # Otherwise, if we're incrementing, take the ceiling, and if we're decrementing, take the floor
            return math.floor(raw_iterations) if step > 0 else math.ceil(raw_iterations)

    @staticmethod
    def merge_configurations(origin: dict, new: dict):
        """Recursively merge `new` into `origin`."""
        for key, value in new.items():
            if key in origin and isinstance(origin[key], dict) and isinstance(value, dict):
                QuantumMachinesCompiler.merge_configurations(origin[key], value)
            else:
                origin[key] = value
        return origin
