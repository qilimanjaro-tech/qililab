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


import math
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import qpysequence as QPy
import qpysequence.program as QPyProgram
import qpysequence.program.instructions as QPyInstructions
from qpysequence.utils.constants import INST_MAX_WAIT

from qililab.config import logger
from qililab.qprogram.blocks import Average, Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.operations import (
    Acquire,
    Measure,
    Operation,
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetMarkers,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.variable import Variable
from qililab.waveforms import IQPair, Square, Waveform


@dataclass
class AcquisitionData:
    """Class representing the output information generated by QbloxCompiler for an acquisition."""

    bus: str
    save_adc: bool


Sequences = dict[str, QPy.Sequence]
Acquisitions = dict[str, dict[str, AcquisitionData]]


class QbloxCompilationOutput:
    """Class representing the output information generated by QbloxCompiler.

    Attributes:
        sequences (Sequence): A dictionary with the buses participating in the QProgram as keys and the corresponding Sequence as values.
        acquisitions (Acquisitions): A dictionary with the buses participating in the acquisitions as keys and the corresponding Acquisitions as values.
    """

    def __init__(self, qprogram: QProgram, sequences: Sequences, acquisitions: Acquisitions):
        self.qprogram = qprogram
        self.sequences = sequences
        self.acquisitions = acquisitions

    def __iter__(self):
        """Allows the class to be unpacked as a tuple (program, config, measurements)."""
        yield self.sequences
        yield self.acquisitions


class BusCompilationInfo:
    """Class representing the information stored by QbloxCompiler for a bus."""

    def __init__(self) -> None:
        # The generated Sequence
        self.qpy_sequence = QPy.Sequence(
            program=QPy.Program(), waveforms=QPy.Waveforms(), acquisitions=QPy.Acquisitions(), weights=QPy.Weights()
        )

        # Acquisitions information
        self.acquisitions: dict[str, AcquisitionData] = {}

        # Dictionaries to hold mappings useful during compilation.
        self.variable_to_register: dict[Variable, QPyProgram.Register] = {}
        self.waveform_to_index: dict[str, int] = {}
        self.weight_to_index: dict[str, int] = {}
        self.acquisition_to_index: dict[str, int] = {}

        # Create and append the main block to the Sequence's program
        main_block = QPyProgram.Block(name="main")
        self.qpy_sequence._program.append_block(main_block)

        # Stacks to manage block hierarchy during compilation
        self.qpy_block_stack: deque[QPyProgram.Block] = deque([main_block])
        self.qprogram_block_stack: deque[Block] = deque()

        # Counters to help with naming and indexing
        self.next_bin_index = 0
        self.next_acquisition_index = 0
        self.loop_counter = 0
        self.average_counter = 0
        self.square_optimization_counter = 0

        # Syncing durations
        self.static_duration = 0
        self.dynamic_durations: list[Variable] = []
        self.sync_durations: list[QPyProgram.Register] = []

        # Syncing marker. If true, a real-time instruction has been added since the last sync or the beginning of the program.
        self.marked_for_sync = False

        # Time of flight. Defaults to minimum_wait_duration and is updated if times_of_flight parameter is provided during compilation.
        self.time_of_flight = QbloxCompiler.minimum_wait_duration

        # Delay. Defaults 0 delay and is updated if delays parameter is provided within the runcard.
        self.delay = 0


class QbloxCompiler:
    """A class for compiling QProgram to QBlox hardware."""

    minimum_wait_duration: int = 4

    def __init__(self) -> None:
        # Handlers to map each operation to a corresponding handler function
        self._handlers: dict[type, Callable] = {
            InfiniteLoop: self._handle_infinite_loop,
            Parallel: self._handle_parallel,
            Average: self._handle_average,
            ForLoop: self._handle_for_loop,
            Loop: self._handle_loop,
            SetFrequency: self._handle_set_frequency,
            SetPhase: self._handle_set_phase,
            ResetPhase: self._handle_reset_phase,
            SetGain: self._handle_set_gain,
            SetOffset: self._handle_set_offset,
            SetMarkers: self._handle_set_markers,
            Wait: self._handle_wait,
            Sync: self._handle_sync,
            Measure: self._handle_measure,
            Acquire: self._handle_acquire,
            Play: self._handle_play,
            Block: self._handle_block,
        }

        self._qprogram: QProgram
        self._buses: dict[str, BusCompilationInfo]
        self._sync_counter: int
        self._voltage_coefficient: dict[str, float] = {}

    def compile(
        self,
        qprogram: QProgram,
        voltage_coefficient: dict[str, float],
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        times_of_flight: dict[str, int] | None = None,
        delays: dict[str, int] | None = None,
        markers: dict[str, str] | None = None,
        optimize_square_waveforms: bool = False,
    ) -> QbloxCompilationOutput:
        """Compile QProgram to qpysequence.Sequence

        Args:
            qprogram (QProgram): The QProgram to be compiled
            voltage_coefficient (dict[str, float]): Coefficient of voltage that depends on the module type and its voltage limit, QRMs reach 1 Vpp and QCMs 5 Vpp.
            bus_mapping (dict[str, str] | None, optional): Optional mapping of bus names. Defaults to None.
            calibration (Calibration | None, optional): . Defaults to None.
            times_of_flight (dict[str, int] | None, optional): Optional time of flight of bus. Defaults to None.
            delays (dict[str, int] | None, optional): . Defaults to None.
            markers (dict[str, str] | None, optional): . Defaults to None.
            optimize_square_waveforms (bool, optional): . Defaults to False.

        Returns:
            QbloxCompilationOutput:
        """

        def traverse(block: Block):
            delay_implemented = False
            for bus in self._buses:
                self._buses[bus].qprogram_block_stack.append(block)
            for element in block.elements:
                if isinstance(element, Play) and not delay_implemented:
                    for bus in self._buses:
                        if self._buses[bus].delay > 0:
                            self._handle_wait(element=Wait(bus=bus, duration=self._buses[bus].delay), delay=True)
                        elif self._buses[bus].delay < 0:
                            for other_buses in self._buses:
                                if other_buses != bus:
                                    self._handle_wait(
                                        element=Wait(bus=other_buses, duration=-self._buses[bus].delay), delay=True
                                    )
                    delay_implemented = True
                handler = self._handlers.get(type(element))
                if not handler:
                    raise NotImplementedError(f"{element.__class__} is currently not supported in QBlox.")
                appended = handler(element)
                if isinstance(element, Block):
                    traverse(element)
                    if not self._qprogram.qblox.disable_autosync and isinstance(
                        element, (ForLoop, Parallel, Loop, Average)
                    ):
                        self._handle_sync(element=Sync(buses=None), delay=True)
                    if appended:
                        for bus in self._buses:
                            self._buses[bus].qpy_block_stack.pop()
            for bus in self._buses:
                self._buses[bus].qprogram_block_stack.pop()

        self._qprogram = qprogram
        if bus_mapping is not None:
            self._qprogram = self._qprogram.with_bus_mapping(bus_mapping=bus_mapping)
        if calibration is not None:
            self._qprogram = self._qprogram.with_calibration(calibration=calibration)
        if self._qprogram.has_calibrated_waveforms_or_weights():
            raise RuntimeError(
                "Cannot compile to hardware-native instructions because QProgram contains named operations that are not mapped. Provide a calibration instance containing all necessary mappings."
            )

        self.optimize_square_waveforms = optimize_square_waveforms
        self._sync_counter = 0
        self._buses = self._populate_buses()
        self._voltage_coefficient = voltage_coefficient

        # Pre-processing: Update time of flight
        if times_of_flight is not None:
            for bus in self._buses.keys() & times_of_flight.keys():
                self._buses[bus].time_of_flight = times_of_flight[bus]

        # Pre-processing: Update delay
        if delays is not None:
            for bus in self._buses.keys() & delays.keys():
                self._buses[bus].delay = delays[bus]

        # Pre-processing: Set markers ON/OFF
        for bus in self._buses:
            mask = markers[bus] if markers is not None and bus in markers else "0000"
            self._buses[bus].qpy_sequence._program.blocks[0].append_component(QPyInstructions.SetMrk(int(mask, 2)))
            self._buses[bus].qpy_sequence._program.blocks[0].append_component(QPyInstructions.UpdParam(4))
            self._buses[bus].static_duration += 4

        # Recursive traversal to convert QProgram blocks to Sequence
        traverse(self._qprogram._body)

        # Post-processing: Set all markers OFF, add stop instructions and compile
        for bus in self._buses:
            self._buses[bus].qpy_block_stack[0].append_component(component=QPyInstructions.SetMrk(0))
            self._buses[bus].qpy_block_stack[0].append_component(component=QPyInstructions.UpdParam(4))
            self._buses[bus].qpy_block_stack[0].append_component(component=QPyInstructions.Stop())
            self._buses[bus].static_duration += 4
            self._buses[bus].qpy_sequence._program.compile()

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        sequences = {bus: bus_info.qpy_sequence for bus, bus_info in self._buses.items()}
        acquisitions = {bus: bus_info.acquisitions for bus, bus_info in self._buses.items()}
        return QbloxCompilationOutput(qprogram=self._qprogram, sequences=sequences, acquisitions=acquisitions)

    def _populate_buses(self):
        """Map each bus in the QProgram to a BusCompilationInfo instance.

        Returns:
            A dictionary where the keys are bus names and the values are BusCompilationInfo objects.
        """

        return {bus: BusCompilationInfo() for bus in self._qprogram.buses}

    def _append_to_waveforms_of_bus(self, bus: str, waveform_I: Waveform, waveform_Q: Waveform | None):
        """Append waveforms to Sequence's Waveforms of the given bus.

        Args:
            bus (str): Name of the bus.
            waveform_I (Waveform): I waveform.
            waveform_Q (Waveform | None): Q waveform.
        """

        def handle_waveform(waveform: Waveform | None, default_length: int = 0):
            _hash = QbloxCompiler._hash_waveform(waveform) if waveform else f"zeros {default_length}"

            if _hash in self._buses[bus].waveform_to_index:
                index = self._buses[bus].waveform_to_index[_hash]
                length = next(
                    len(waveform.data)
                    for waveform in self._buses[bus].qpy_sequence._waveforms._waveforms
                    if waveform.index == index
                )
                return index, length

            envelope = waveform.envelope() / self._voltage_coefficient[bus] if waveform else np.zeros(default_length)
            index = self._buses[bus].qpy_sequence._waveforms.add(envelope)
            self._buses[bus].waveform_to_index[_hash] = index
            return index, len(envelope)

        index_I, length_I = handle_waveform(waveform_I, 0)
        index_Q, _ = handle_waveform(waveform_Q, len(waveform_I.envelope()))
        return index_I, index_Q, length_I

    def _append_to_weights_of_bus(self, bus: str, weights: IQPair):
        def handle_weight(waveform: Waveform):
            _hash = QbloxCompiler._hash_waveform(waveform)

            if _hash in self._buses[bus].weight_to_index:
                index = self._buses[bus].weight_to_index[_hash]
                length = next(
                    len(weight.data)
                    for weight in self._buses[bus].qpy_sequence._weights._weights
                    if weight.index == index
                )
                return index, length

            envelope = waveform.envelope()
            length = len(envelope)
            index = self._buses[bus].qpy_sequence._weights.add(envelope)
            self._buses[bus].weight_to_index[_hash] = index
            return index, length

        index_I, length_I = handle_weight(weights.I)
        index_Q, _ = handle_weight(weights.Q)
        return index_I, index_Q, length_I

    def _handle_parallel(self, element: Parallel):
        if not element.loops:
            raise NotImplementedError("Parallel block should contain loops.")
        if any(isinstance(loop, Loop) for loop in element.loops):
            raise NotImplementedError("Loops with arbitrary numpy arrays are not currently supported for QBlox.")

        loops = []
        iterations = []
        for loop in element.loops:
            operation = QbloxCompiler._get_reference_operation_of_loop(loop=loop, starting_block=element)
            start, step, iters = QbloxCompiler._convert_for_loop_values(loop, operation)  # type: ignore[arg-type]
            loops.append((start, step))
            iterations.append(iters)
        iterations = min(iterations)

        # iterations = min(QbloxCompiler._calculate_iterations(loop.start, loop.stop, loop.step) for loop in element.loops)
        # loops = [(QbloxCompiler._convert_for_loop_values(for_loop=loop, operation=QbloxCompiler._get_reference_operation_of_loop(element)))[:2]) for loop in element.loops]

        for bus in self._buses:
            qpy_loop = QPyProgram.IterativeLoop(
                name=f"loop_{self._buses[bus].loop_counter}", iterations=iterations, loops=loops
            )
            for i, loop in enumerate(element.loops):
                self._buses[bus].variable_to_register[loop.variable] = qpy_loop.loop_registers[i]
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].loop_counter += 1
        return True

    def _handle_average(self, element: Average):
        for bus in self._buses:
            qpy_loop = QPyProgram.Loop(name=f"avg_{self._buses[bus].average_counter}", begin=element.shots)
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].average_counter += 1
        return True

    def _handle_infinite_loop(self, _: InfiniteLoop):
        for bus in self._buses:
            qpy_loop = QPyProgram.InfiniteLoop(name=f"infinite_loop_{self._buses[bus].loop_counter}")
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].loop_counter += 1
        return True

    def _handle_for_loop(self, element: ForLoop):
        operation = QbloxCompiler._get_reference_operation_of_loop(element)
        start, step, iterations = QbloxCompiler._convert_for_loop_values(element, operation)
        for bus in self._buses:
            qpy_loop = QPyProgram.IterativeLoop(
                name=f"loop_{self._buses[bus].loop_counter}", iterations=iterations, loops=[(start, step)]
            )
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].variable_to_register[element.variable] = qpy_loop.loop_registers[0]
            self._buses[bus].loop_counter += 1
        return True

    def _handle_loop(self, _: Loop):
        raise NotImplementedError("Loops with arbitrary numpy arrays are not currently supported for QBlox.")

    def _handle_set_frequency(self, element: SetFrequency):
        convert = QbloxCompiler._convert_value(element)
        frequency = (
            self._buses[element.bus].variable_to_register[element.frequency]
            if isinstance(element.frequency, Variable)
            else convert(element.frequency)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetFreq(frequency=frequency)
        )

    def _handle_set_phase(self, element: SetPhase):
        convert = QbloxCompiler._convert_value(element)
        phase = (
            self._buses[element.bus].variable_to_register[element.phase]
            if isinstance(element.phase, Variable)
            else convert(element.phase)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(component=QPyInstructions.SetPh(phase=phase))

    def _handle_reset_phase(self, element: ResetPhase):
        self._buses[element.bus].qpy_block_stack[-1].append_component(component=QPyInstructions.ResetPh())

    def _handle_set_gain(self, element: SetGain):
        convert = QbloxCompiler._convert_value(element)
        gain = (
            self._buses[element.bus].variable_to_register[element.gain]
            if isinstance(element.gain, Variable)
            else convert(element.gain)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetAwgGain(gain_0=gain, gain_1=gain)
        )

    def _handle_set_offset(self, element: SetOffset):
        convert = QbloxCompiler._convert_value(element)
        offset_0 = (
            self._buses[element.bus].variable_to_register[element.offset_path0]
            if isinstance(element.offset_path0, Variable)
            else convert(element.offset_path0)
        )
        if element.offset_path1 is None:
            raise ValueError("No offset has been given for path 1 inside set_offset.")
        offset_1 = (
            self._buses[element.bus].variable_to_register[element.offset_path1]  # type: ignore[index]
            if isinstance(element.offset_path1, Variable)
            else convert(element.offset_path1)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetAwgOffs(offset_0=offset_0, offset_1=offset_1)
        )

    def _handle_set_markers(self, element: SetMarkers):
        marker_outputs = int(element.mask, 2)
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetMrk(marker_outputs=marker_outputs)
        )

    def _handle_wait(self, element: Wait, delay: bool = False):
        duration: QPyProgram.Register | int
        if isinstance(element.duration, Variable):
            duration = self._buses[element.bus].variable_to_register[element.duration]
            self._buses[element.bus].dynamic_durations.append(element.duration)
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Wait(wait_time=duration)
            )
        else:
            convert = QbloxCompiler._convert_value(element)
            duration = convert(element.duration)
            if not delay:
                self._buses[element.bus].static_duration += duration
            # loop over wait instructions if static duration is longer than allowed qblox max wait time of 2**16 -4
            self._handle_add_waits(bus=element.bus, duration=duration)

        self._buses[element.bus].marked_for_sync = True

    def _handle_add_waits(self, bus: str, duration: int):
        """Wait for longer than QBLOX INST_MAX_WAIT by looping over wait instructions

        Args:
            element (Wait): wait element
            duration (int): duration to wait in ns
        """
        if duration > INST_MAX_WAIT:
            for _ in range(duration // INST_MAX_WAIT):
                self._buses[bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Wait(wait_time=INST_MAX_WAIT)
                )
        # add the remaining wait time (or all of it if the above conditional is false)
        self._buses[bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.Wait(wait_time=duration % INST_MAX_WAIT)
        )

    def _handle_sync(self, element: Sync, delay: bool = False):
        # Get the buses involved in the sync operation.
        buses = set(element.buses or self._buses)

        # If they are zero or one, return.
        if len(buses) <= 1:
            return

        # If there is no bus marked for sync, return.
        if all(not self._buses[bus].marked_for_sync for bus in buses):
            return

        # Is there any bus that has dynamic durations?
        if any(bus for bus in buses if self._buses[bus].dynamic_durations or self._buses[bus].sync_durations):
            # If yes, we must add a sync block that calculates the difference between buses dynamically.
            # But the following doesn't work unfortunetely, so raise an error for now.
            self.__handle_dynamic_sync(buses=buses)
        else:
            # If no, calculating the difference is trivial.
            self.__handle_static_sync(buses=buses, delay=delay)

        # In any case, mark al buses as synced.
        for bus in buses:
            self._buses[bus].marked_for_sync = False

    def __handle_static_sync(self, buses: set[str], delay: bool = False):
        max_duration = max(self._buses[bus].static_duration for bus in buses)
        if delay:
            max_delay = max(self._buses[bus].delay for bus in buses)
        for bus in buses:
            if delay:
                delay_diff = max_delay - self._buses[bus].delay
                duration_diff = max_duration - self._buses[bus].static_duration + delay_diff
            else:
                duration_diff = max_duration - self._buses[bus].static_duration
            if duration_diff > 0:
                # loop over wait instructions if static duration is longer than allowed qblox max wait time of 2**16 -4
                self._handle_add_waits(bus=bus, duration=duration_diff)
                self._buses[bus].static_duration += duration_diff

    def __handle_dynamic_sync(self, buses: set[str]):
        raise NotImplementedError("Dynamic syncing is not implemented yet.")

    def _handle_measure(self, element: Measure):
        """Wrapper for qblox play and acquire methods to be called in a single operation for consistency with QuantumMachines
        measure operation

        Args:
            element (Measure): measure operation
        """
        time_of_flight = self._buses[element.bus].time_of_flight
        play = Play(bus=element.bus, waveform=element.waveform, wait_time=time_of_flight)
        acquire = Acquire(bus=element.bus, weights=element.weights, save_adc=element.save_adc)
        self._handle_play(play)
        self._handle_acquire(acquire)

    def _handle_acquire(self, element: Acquire):
        # TODO: unify with measure when time of flight is implemented
        loops = [
            (i, loop)
            for i, loop in enumerate(self._buses[element.bus].qpy_block_stack)
            if isinstance(loop, QPyProgram.IterativeLoop) and not loop.name.startswith("avg")
        ]
        num_bins = math.prod(loop[1].iterations for loop in loops)
        acquisition_name = f"acquisition_{self._buses[element.bus].next_acquisition_index}"
        self._buses[element.bus].qpy_sequence._acquisitions.add(
            name=acquisition_name,
            num_bins=num_bins,
            index=self._buses[element.bus].next_acquisition_index,
        )
        self._buses[element.bus].acquisitions[acquisition_name] = AcquisitionData(
            bus=element.bus, save_adc=element.save_adc
        )

        index_I, index_Q, integration_length = self._append_to_weights_of_bus(element.bus, weights=element.weights)

        if num_bins == 1:
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.AcquireWeighed(
                    acq_index=self._buses[element.bus].next_acquisition_index,
                    bin_index=self._buses[element.bus].next_bin_index,
                    weight_index_0=index_I,
                    weight_index_1=index_Q,
                    wait_time=integration_length,
                )
            )
        else:
            bin_register = QPyProgram.Register()
            block_index_for_move_instruction = loops[0][0] - 1 if loops else -2
            block_index_for_add_instruction = loops[-1][0] if loops else -1
            self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].append_component(
                component=QPyInstructions.Move(var=self._buses[element.bus].next_bin_index, register=bin_register),
                bot_position=len(self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].components),
            )
            register_I, register_Q = QPyProgram.Register(), QPyProgram.Register()
            self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].append_component(
                component=QPyInstructions.Move(var=index_I, register=register_I),
                bot_position=len(self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].components),
            )
            self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].append_component(
                component=QPyInstructions.Move(var=index_Q, register=register_Q),
                bot_position=len(self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].components),
            )
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.AcquireWeighed(
                    acq_index=self._buses[element.bus].next_acquisition_index,
                    bin_index=bin_register,
                    weight_index_0=register_I,
                    weight_index_1=register_Q,
                    wait_time=integration_length,
                )
            )
            self._buses[element.bus].qpy_block_stack[block_index_for_add_instruction].append_component(
                component=QPyInstructions.Add(origin=bin_register, var=1, destination=bin_register)
            )
        self._buses[element.bus].static_duration += integration_length
        self._buses[element.bus].next_bin_index = 0  # maybe this counter can be removed completely
        self._buses[element.bus].next_acquisition_index += 1
        self._buses[element.bus].marked_for_sync = True

    def _handle_play(self, element: Play):
        waveform_I, waveform_Q = element.get_waveforms()
        waveform_variables = element.get_waveform_variables()
        if waveform_variables:
            logger.error("Variables in waveforms are not supported in Qblox.")
            return
        if element.wait_time:
            # The qp.qblox.play() was used. Don't apply optimizations
            index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
            convert = QbloxCompiler._convert_value(element)
            duration = convert(element.wait_time)
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Play(index_I, index_Q, wait_time=duration)
            )
        elif (
            self.optimize_square_waveforms
            and isinstance(waveform_I, Square)
            and (waveform_Q is None or isinstance(waveform_Q, Square))
            and (waveform_I.duration >= 100)
        ):
            duration = waveform_I.duration
            chunk_duration, iterations, remainder = QbloxCompiler.calculate_square_waveform_optimization_values(
                duration
            )
            waveform_I.duration = chunk_duration
            if isinstance(waveform_Q, Square):
                waveform_Q.duration = chunk_duration
            index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
            loop = QPyProgram.IterativeLoop(
                name=f"square_{self._buses[element.bus].square_optimization_counter}", iterations=iterations
            )
            loop.append_component(component=QPyInstructions.Play(index_I, index_Q, wait_time=chunk_duration))
            self._buses[element.bus].qpy_block_stack[-1].append_component(component=loop)
            if remainder != 0:
                waveform_I.duration = remainder
                if isinstance(waveform_Q, Square):
                    waveform_Q.duration = remainder
                index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                    bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
                )
                self._buses[element.bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Play(index_I, index_Q, wait_time=remainder)
                )
            self._buses[element.bus].square_optimization_counter += 1
        else:
            index_I, index_Q, duration = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Play(index_I, index_Q, wait_time=duration)
            )
        self._buses[element.bus].static_duration += duration
        self._buses[element.bus].marked_for_sync = True

    def _handle_block(self, element: Block):
        pass

    @staticmethod
    def _get_reference_operation_of_loop(loop: Loop | ForLoop, starting_block: Block | None = None):
        def collect_operations(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_operations(element)
                elif any(variable == loop.variable for variable in element.get_variables()):
                    yield element

        starting_block = starting_block or loop
        operations = list(collect_operations(starting_block))

        if not operations:
            return None
        if isinstance(operations[0], Play) and operations[0].get_waveform_variables():
            raise NotImplementedError("TODO: Variables referenced in a loop cannot be used in Play operation.")
        return operations[0]

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

    @staticmethod
    def _convert_for_loop_values(for_loop: ForLoop, operation: Operation):
        convert = QbloxCompiler._convert_value(operation)
        iterations = QbloxCompiler._calculate_iterations(start=for_loop.start, stop=for_loop.stop, step=for_loop.step)
        qblox_start = convert(for_loop.start)
        qblox_stop = convert(for_loop.stop)
        qblox_step = (qblox_stop - qblox_start) // (iterations - 1)
        return (qblox_start, qblox_step, iterations)

    @staticmethod
    def _convert_value(operation: Operation) -> Callable[[Any], int]:
        conversion_map: dict[type[Operation], Callable[[Any], int]] = {
            SetFrequency: lambda x: int(x * 4),
            SetPhase: lambda x: int(x * 1e9 / (2 * np.pi)),
            SetGain: lambda x: int(x * 32_767),
            SetOffset: lambda x: int(x * 32_767),
            Wait: lambda x: int(max(x, QbloxCompiler.minimum_wait_duration)),
            Play: lambda x: int(max(x, QbloxCompiler.minimum_wait_duration)),
        }
        return conversion_map.get(type(operation), lambda x: int(x))

    @staticmethod
    def _hash_waveform(waveform: Waveform):
        hashes = {
            key: (value.__dict__ if isinstance(value, Waveform) else value) for key, value in waveform.__dict__.items()
        }
        return f"{waveform.__class__.__name__} {hashes}"

    @staticmethod
    def calculate_square_waveform_optimization_values(duration):
        def remainder_conditions(chunk_duration):
            remainder = duration % chunk_duration
            return remainder, (chunk_duration >= 4 and (remainder == 0 or remainder >= 4))

        def find_chunk_duration(condition_func):
            for chunk_duration in range(100, 501):
                if chunk_duration <= duration:
                    remainder, valid = remainder_conditions(chunk_duration)
                    if valid and condition_func(remainder):
                        return chunk_duration
            return None

        # First try for remainder == 0
        final_chunk_duration = find_chunk_duration(lambda rem: rem == 0)
        if final_chunk_duration is not None:
            return final_chunk_duration, duration // final_chunk_duration, duration % final_chunk_duration

        # If not found, try for remainder ≥ 4
        final_chunk_duration = find_chunk_duration(lambda rem: rem >= 4)
        if final_chunk_duration is not None:
            return final_chunk_duration, duration // final_chunk_duration, duration % final_chunk_duration

        # If no suitable piece_duration found, fallback to entire duration
        return duration, 1, 0
