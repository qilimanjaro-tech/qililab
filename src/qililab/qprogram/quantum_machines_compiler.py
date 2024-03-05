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

import hashlib
import math
from collections import deque
from typing import Callable

import numpy as np
from qm import qua
from qm.qua import _dsl as qua_dsl
from qualang_tools.config.integration_weights_tools import convert_integration_weights

from qililab.qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qililab.qprogram.blocks.infinite_loop import InfiniteLoop
from qililab.qprogram.operations import Measure, Play, ResetPhase, SetFrequency, SetGain, SetPhase, Sync, Wait
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.variable import Domain, Variable
from qililab.waveforms import IQPair, Square, Waveform

# mypy: disable-error-code="operator"


class _BusCompilationInfo:  # pylint: disable=too-few-public-methods
    def __init__(self) -> None:
        self.current_gain: float | qua.QuaVariableType | None = None


class _MeasurementCompilationInfo:  # pylint: disable=too-few-public-methods, too-many-instance-attributes
    def __init__(
        self,
        bus: str,
        variable_I: qua.QuaVariableType | None = None,
        variable_Q: qua.QuaVariableType | None = None,
        stream_I: qua_dsl._ResultSource | None = None,
        stream_Q: qua_dsl._ResultSource | None = None,
        stream_raw_adc: qua_dsl._ResultSource | None = None,
    ) -> None:
        self.bus: str = bus
        self.variable_I: qua.QuaVariableType | None = variable_I
        self.variable_Q: qua.QuaVariableType | None = variable_Q
        self.stream_I: qua_dsl._ResultSource | None = stream_I
        self.stream_Q: qua_dsl._ResultSource | None = stream_Q
        self.stream_raw_adc: qua_dsl._ResultSource | None = stream_raw_adc
        self.loops_iterations: list[int] = []
        self.average: bool = False


class MeasurementInfo:  # pylint: disable=too-few-public-methods
    """Class representing information about the measurements taking place."""

    def __init__(self, bus: str, result_handles: list[str]):
        self.bus: str = bus
        self.result_handles: list[str] = result_handles


class QuantumMachinesCompiler:  # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """A class for compiling QProgram to Quantum Machines hardware."""

    FREQUENCY_COEFF = 1
    PHASE_COEFF = 2 * np.pi
    VOLTAGE_COEFF = 2
    MINIMUM_TIME = 4

    def __init__(self) -> None:
        # Handlers to map each operation to a corresponding handler function
        self._handlers: dict[type, Callable] = {
            InfiniteLoop: self._handle_infinite_loop,
            Parallel: self._handle_parallel_loop,
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
        self._bus_mapping: dict[str, str] | None
        self._qprogram_block_stack: deque[Block]
        self._qprogram_to_qua_variables: dict[Variable, qua.QuaVariableType]
        self._measurements: list[_MeasurementCompilationInfo]
        self._configuration: dict
        self._buses: dict[str, _BusCompilationInfo]

    def compile(
        self, qprogram: QProgram, bus_mapping: dict[str, str] | None = None
    ) -> tuple[qua.Program, dict, list[MeasurementInfo]]:
        """Compile QProgram to QUA's Program.

        Args:
            qprogram (QProgram): The QProgram to be compiled
            bus_mapping (dict[str, str] | None, optional): Optional mapping of bus names. Defaults to None.

        Returns:
            tuple[qua.Program, dict, list[MeasurementInfo]]: A tuple consisting of the generated QUA program, the generated configuration and a list of measurements' information.
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
                else:
                    handler(element)
            self._qprogram_block_stack.pop()

        self._qprogram = qprogram
        self._bus_mapping = bus_mapping

        self._qprogram_block_stack = deque()
        self._qprogram_to_qua_variables = {}
        self._measurements = []
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
            # Recursive traversal to convert QProgram to QUA program.
            traverse(self._qprogram.body)
            # Stream Processing
            with qua.stream_processing():
                measurements = self._process_measurements()

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        return qua_program, self._configuration, measurements

    def _process_measurements(self):
        def _process_measurement(measurement: _MeasurementCompilationInfo, index: int):
            result_handles: list[str] = []

            def _process_stream(stream: qua_dsl._ResultSource, save_as: str) -> None:
                processing_stream: qua_dsl._ResultSource | qua_dsl._ResultStream = stream
                for loop_iteration in measurement.loops_iterations:
                    processing_stream = processing_stream.buffer(loop_iteration)
                if measurement.average:
                    processing_stream = processing_stream.average()
                processing_stream.save(save_as)
                result_handles.append(save_as)

            if measurement.stream_I is not None:
                _process_stream(measurement.stream_I, f"I_{index}")
            if measurement.stream_Q is not None:
                _process_stream(measurement.stream_Q, f"Q_{index}")
            if measurement.stream_raw_adc is not None:
                # TODO: Check if both inputs are available
                _process_stream(measurement.stream_raw_adc.input1(), f"adc1_{index}")
                _process_stream(measurement.stream_raw_adc.input2(), f"adc2_{index}")

            return result_handles

        measurements = [
            MeasurementInfo(bus=measurement.bus, result_handles=_process_measurement(measurement=measurement, index=i))
            for i, measurement in enumerate(self._measurements)
        ]

        return measurements

    def _declare_variables(self):
        for variable in self._qprogram.variables:
            if variable.domain in [Domain.Time, Domain.Frequency]:
                qua_variable = qua.declare(int)
            else:
                qua_variable = qua.declare(qua.fixed)
            self._qprogram_to_qua_variables[variable] = qua_variable

    def _populate_buses(self):
        """Map each bus in the QProgram to a BusCompilationInfo instance."""

        buses = set(
            self._bus_mapping[bus] if self._bus_mapping and bus in self._bus_mapping else bus
            for bus in self._qprogram.buses
        )
        self._configuration["elements"] = {bus: {"operations": {}} for bus in buses}
        self._buses = {bus: _BusCompilationInfo() for bus in buses}

    def _handle_infinite_loop(self, _: InfiniteLoop):
        return qua.infinite_loop_()

    def _handle_parallel_loop(self, element: Parallel):
        variables = []
        loops = []
        for loop in element.loops:
            qua_variable = self._qprogram_to_qua_variables[loop.variable]
            values = (
                np.arange(loop.start, loop.stop + loop.step / 2, loop.step)
                if isinstance(loop, ForLoop)
                else loop.values
            )
            if loop.variable.domain is Domain.Phase:
                values = values / self.PHASE_COEFF
            if loop.variable.domain is Domain.Frequency:
                values = values.astype(int)
            if loop.variable.domain is Domain.Time:
                values = np.maximum(values, self.MINIMUM_TIME).astype(int)

            variables.append(qua_variable)
            loops.append(values)
        return qua.for_each_(tuple(variables), tuple(loops))

    def _handle_for_loop(self, element: ForLoop):
        qua_variable = self._qprogram_to_qua_variables[element.variable]
        start, stop, step = element.start, element.stop, element.step
        if element.variable.domain is Domain.Phase:
            start, stop, step = start / self.PHASE_COEFF, stop / self.PHASE_COEFF, step / self.PHASE_COEFF
        if element.variable.domain is Domain.Frequency:
            start, stop, step = (
                int(start),
                int(stop),
                int(step),
            )
        if element.variable.domain is Domain.Time:
            start = max(start, self.MINIMUM_TIME)

        to_positive = stop >= start
        if to_positive:
            return qua.for_(qua_variable, start, qua_variable <= stop, qua_variable + step)
        return qua.for_(qua_variable, start, qua_variable >= stop, qua_variable + step)

    def _handle_loop(self, element: Loop):
        qua_variable = self._qprogram_to_qua_variables[element.variable]
        values = element.values
        if element.variable.domain is Domain.Phase:
            values = values / self.PHASE_COEFF
        if element.variable.domain is Domain.Frequency:
            values = values.astype(int)
        if element.variable.domain is Domain.Time:
            values = np.maximum(values, self.MINIMUM_TIME).astype(int)
        return qua.for_each_(qua_variable, values.tolist())

    def _handle_average(self, element: Average):
        variable = qua.declare(int)
        return qua.for_(variable, 0, variable < element.shots, variable + 1)

    def _handle_set_frequency(self, element: SetFrequency):
        bus = self._bus_mapping[element.bus] if self._bus_mapping and element.bus in self._bus_mapping else element.bus
        frequency = (
            self._qprogram_to_qua_variables[element.frequency]
            if isinstance(element.frequency, Variable)
            else element.frequency
        )
        qua.update_frequency(element=bus, new_frequency=frequency)

    def _handle_set_phase(self, element: SetPhase):
        bus = self._bus_mapping[element.bus] if self._bus_mapping and element.bus in self._bus_mapping else element.bus
        phase = (
            self._qprogram_to_qua_variables[element.phase]
            if isinstance(element.phase, Variable)
            else element.phase / self.PHASE_COEFF
        )
        qua.frame_rotation_2pi(phase, bus)

    def _handle_reset_phase(self, element: ResetPhase):
        bus = self._bus_mapping[element.bus] if self._bus_mapping and element.bus in self._bus_mapping else element.bus
        qua.reset_frame(bus)

    def _handle_set_gain(self, element: SetGain):
        bus = self._bus_mapping[element.bus] if self._bus_mapping and element.bus in self._bus_mapping else element.bus
        gain = self._qprogram_to_qua_variables[element.gain] if isinstance(element.gain, Variable) else element.gain
        # QUA doesn't have a method for setting the gain directly.
        # Instead, it uses an amplitude multiplication with `amp()`.
        # Thus, we store the current gain to multiply with in the next play instructions.
        self._buses[bus].current_gain = gain

    def _handle_play(self, element: Play):
        bus = self._bus_mapping[element.bus] if self._bus_mapping and element.bus in self._bus_mapping else element.bus
        waveform_I, waveform_Q = element.get_waveforms()
        waveform_variables = element.get_waveform_variables()
        duration = waveform_I.get_duration()

        gain = (
            qua.amp(self._buses[bus].current_gain * self.VOLTAGE_COEFF)
            if self._buses[bus].current_gain is not None
            else None
        )

        if not waveform_variables:
            waveform_I_name = self.__add_waveform_to_configuration(waveform_I)
            waveform_Q_name = self.__add_waveform_to_configuration(waveform_Q) if waveform_Q else None
            pulse_name = self.__add_or_update_control_pulse_to_configuration(waveform_I_name, waveform_Q_name, duration)
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = operation_name * gain if gain is not None else operation_name
            qua.play(pulse, bus)

    def _handle_measure(
        self, element: Measure
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        bus = self._bus_mapping[element.bus] if self._bus_mapping and element.bus in self._bus_mapping else element.bus
        waveform_I, waveform_Q = element.get_waveforms()

        waveform_I_name = self.__add_waveform_to_configuration(waveform_I)
        waveform_Q_name = self.__add_waveform_to_configuration(waveform_Q)

        gain = (
            qua.amp(self._buses[bus].current_gain * self.VOLTAGE_COEFF)
            if self._buses[bus].current_gain is not None
            else None
        )

        variable_I, variable_Q, stream_I, stream_Q, stream_raw_adc = None, None, None, None, None

        if element.save_raw_adc:
            stream_raw_adc = qua.declare_stream(adc_trace=True)

        if element.weights is None:
            pulse_name = self.__add_or_update_measurement_pulse_to_configuration(
                waveform_I_name, waveform_Q_name, duration=waveform_I.get_duration(), integration_weights=[]
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = operation_name * gain if gain is not None else operation_name
            qua.measure(pulse, element.bus, stream_raw_adc)
        elif isinstance(element.weights, IQPair):
            variable_I = qua.declare(qua.fixed)
            stream_I = qua.declare_stream()
            weight_I = self.__add_integration_weight_to_configuration(element.weights.I, element.weights.Q)
            pulse_name = self.__add_or_update_measurement_pulse_to_configuration(
                waveform_I_name, waveform_Q_name, duration=waveform_I.get_duration(), integration_weights=[weight_I]
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = operation_name * gain if gain is not None else operation_name
            if element.demodulation:
                qua.measure(pulse, bus, stream_raw_adc, qua.demod.full(weight_I, variable_I, "out1"))
            else:
                qua.measure(pulse, bus, stream_raw_adc, qua.integration.full(weight_I, variable_I, "out1"))
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
                duration=waveform_I.get_duration(),
                integration_weights=[weight_I, weight_Q],
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = operation_name * gain if gain is not None else operation_name
            if element.demodulation:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.demod.full(weight_I, variable_I, "out1"),
                    qua.demod.full(weight_Q, variable_Q, "out2"),
                )
            else:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.integration.full(weight_I, variable_I, "out1"),
                    qua.integration.full(weight_Q, variable_Q, "out2"),
                )
            qua.save(variable_I, stream_I)
            qua.save(variable_Q, stream_Q)
        elif isinstance(element.weights, tuple) and len(element.weights) == 4:
            variable_I = qua.declare(qua.fixed)
            variable_Q = qua.declare(qua.fixed)
            stream_I = qua.declare_stream()
            stream_Q = qua.declare_stream()
            weight_A = self.__add_integration_weight_to_configuration(element.weights[0].I, element.weights[0].Q)
            weight_B = self.__add_integration_weight_to_configuration(element.weights[1].I, element.weights[1].Q)
            weight_C = self.__add_integration_weight_to_configuration(element.weights[2].I, element.weights[2].Q)  # type: ignore[misc]
            weight_D = self.__add_integration_weight_to_configuration(element.weights[3].I, element.weights[3].Q)  # type: ignore[misc]
            pulse_name = self.__add_or_update_measurement_pulse_to_configuration(
                waveform_I_name,
                waveform_Q_name,
                duration=waveform_I.get_duration(),
                integration_weights=[weight_A, weight_B, weight_C, weight_D],
            )
            operation_name = self.__add_pulse_to_element_operations(bus, pulse_name)
            pulse = operation_name * gain if gain is not None else operation_name
            if element.demodulation:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.dual_demod.full(weight_A, "out1", weight_B, "out2", variable_I),
                    qua.dual_demod.full(weight_C, "out1", weight_D, "out2", variable_Q),
                )
            else:
                qua.measure(
                    pulse,
                    bus,
                    stream_raw_adc,
                    qua.dual_integration.full(weight_A, "out1", weight_B, "out2", variable_I),
                    qua.dual_integration.full(weight_C, "out1", weight_D, "out2", variable_Q),
                )
            qua.save(variable_I, stream_I)
            qua.save(variable_Q, stream_Q)

        measurement_info = _MeasurementCompilationInfo(bus, variable_I, variable_Q, stream_I, stream_Q, stream_raw_adc)
        for block in reversed(self._qprogram_block_stack):
            if isinstance(block, ForLoop):
                iterations = QuantumMachinesCompiler._calculate_iterations(block.start, block.stop, block.step)
                measurement_info.loops_iterations.append(iterations)
            if isinstance(block, Loop):
                iterations = len(block.values)
                measurement_info.loops_iterations.append(iterations)
            if isinstance(block, Parallel):
                iterations = min(
                    len(loop.values)
                    if isinstance(loop, Loop)
                    else QuantumMachinesCompiler._calculate_iterations(loop.start, loop.stop, loop.step)
                    for loop in block.loops
                )
                measurement_info.loops_iterations.append(iterations)
            if isinstance(block, Average):
                measurement_info.average = True

        self._measurements.append(measurement_info)

    def _handle_wait(self, element: Wait):
        bus = self._bus_mapping[element.bus] if self._bus_mapping and element.bus in self._bus_mapping else element.bus
        duration = (
            self._qprogram_to_qua_variables[element.duration]
            if isinstance(element.duration, Variable)
            else max(element.duration, self.MINIMUM_TIME)
        )
        qua.wait(duration, bus)

    def _handle_sync(self, element: Sync):
        if element.buses:
            buses = [
                self._bus_mapping[bus] if self._bus_mapping and bus in self._bus_mapping else bus
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
            self._configuration["pulses"][pulse_name]["integration_weights"].update(
                {weight: weight for weight in integration_weights}
            )
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
            amplitude = waveform.amplitude / QuantumMachinesCompiler.VOLTAGE_COEFF
            return {"type": "constant", "sample": amplitude}

        envelope = waveform.envelope() / QuantumMachinesCompiler.VOLTAGE_COEFF
        return {"type": "arbitrary", "samples": envelope.tolist()}

    @staticmethod
    def __integration_weight_to_config(cosine_part: Waveform, sine_part: Waveform):
        cosine_envelope, sine_envelope = cosine_part.envelope(resolution=4), sine_part.envelope(resolution=4)
        converted_cosine_part = convert_integration_weights(integration_weights=cosine_envelope, N=len(cosine_envelope))
        converted_sine_part = convert_integration_weights(integration_weights=sine_envelope, N=len(sine_envelope))

        return {"cosine": converted_cosine_part, "sine": converted_sine_part}

    @staticmethod
    def _calculate_iterations(start: int | float, stop: int | float, step: int | float):
        if step == 0:
            raise ValueError("Step value cannot be zero")

        # Calculate the raw number of iterations
        raw_iterations = (stop - start + step) / step

        # If the raw number of iterations is very close to an integer, round it to that integer
        # This accounts for potential floating-point inaccuracies
        if abs(raw_iterations - round(raw_iterations)) < 1e-9:
            return round(raw_iterations)

        # Otherwise, if we're incrementing, take the ceiling, and if we're decrementing, take the floor
        return math.floor(raw_iterations) if step > 0 else math.ceil(raw_iterations)
