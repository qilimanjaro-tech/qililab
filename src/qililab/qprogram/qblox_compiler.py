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

# pylint: disable=protected-access
import math
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID

import numpy as np
import qpysequence as QPy
import qpysequence.program as QPyProgram
import qpysequence.program.instructions as QPyInstructions
from qpysequence.utils.constants import INST_MAX_WAIT

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
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.variable import Domain, Variable
from qililab.waveforms import IQPair, Waveform


@dataclass
class AcquisitionData:
    """Class representing the output information generated by QbloxCompiler for an acquisition."""

    save_adc: bool


Sequences = dict[str, QPy.Sequence]
Acquisitions = dict[str, dict[str, AcquisitionData]]


class BusCompilationInfo:  # pylint: disable=too-many-instance-attributes, too-few-public-methods
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
        self.waveform_to_register: dict[Waveform, QPyProgram.Register] = {}

        self._allocated_registers_of_block: dict[UUID, list[QPyProgram.Register]] = {}

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

        # Syncing durations
        self.static_duration = 0
        self.dynamic_durations: list[Variable] = []
        self.sync_durations: list[QPyProgram.Register] = []

        # Syncing marker. If true, a real-time instruction has been added since the last sync or the beginning of the program.
        self.marked_for_sync = False

        # Time of flight. Defaults to minimum_wait_duration and is updated if times_of_flight parameter is provided during compilation.
        self.time_of_flight = QbloxCompiler.minimum_wait_duration


class QbloxCompiler:  # pylint: disable=too-few-public-methods
    """A class for compiling QProgram to QBlox hardware."""

    minimum_wait_duration: int = 4
    FREQUENCY_COEFF = 4
    PHASE_COEFF = 1e9 / (2 * np.pi)
    VOLTAGE_COEFF = 32_767
    MINIMUM_TIME = 4

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
            Wait: self._handle_wait,
            Sync: self._handle_sync,
            Measure: self._handle_measure,
            Acquire: self._handle_acquire,
            Play: self._handle_play,
        }

        self._qprogram: QProgram
        self._buses: dict[str, BusCompilationInfo]
        self._sync_counter: int

    def compile(
        self,
        qprogram: QProgram,
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        times_of_flight: dict[str, int] | None = None,
    ) -> tuple[Sequences, Acquisitions]:
        """Compile QProgram to qpysequence.Sequence

        Args:
            qprogram (QProgram): The QProgram to be compiled
            bus_mapping (dict[str, str] | None, optional): Optional mapping of bus names. Defaults to None.
            times_of_flight (dict[str, int] | None, optional): Optional time of flight of bus. Defaults to None.

        Returns:
            dict[str, QPy.Sequence]: A dictionary with the buses participating in the QProgram as keys and the corresponding Sequence as values.
        """

        def traverse(block: Block):
            for bus in self._buses:
                self._buses[bus].qprogram_block_stack.append(block)
            for element in block.elements:
                handler = self._handlers.get(type(element))
                if not handler:
                    raise NotImplementedError(f"{element.__class__} is currently not supported in QBlox.")
                appended = handler(element)
                if isinstance(element, Block):
                    traverse(element)
                    if not self._qprogram.qblox.disable_autosync and isinstance(
                        element, (ForLoop, Parallel, Loop, Average)
                    ):
                        self._handle_sync(element=Sync(buses=None))
                    if appended:
                        for bus in self._buses:
                            self._buses[bus].qpy_block_stack.pop()
            for bus in self._buses:
                self._buses[bus].qprogram_block_stack.pop()
                if block._uuid in self._buses[bus]._allocated_registers_of_block:
                    for register in self._buses[bus]._allocated_registers_of_block[block._uuid]:
                        self._buses[bus].qpy_sequence._program._memory.mark_out_of_scope(register)
                    del self._buses[bus]._allocated_registers_of_block[block._uuid]

        self._qprogram = qprogram
        if bus_mapping is not None:
            self._qprogram = self._qprogram.with_bus_mapping(bus_mapping=bus_mapping)
        if calibration is not None:
            self._qprogram = self._qprogram.with_calibration(calibration=calibration)
        if self._qprogram.has_calibrated_waveforms_or_weights():
            raise RuntimeError(
                "Cannot compile to hardware-native instructions because QProgram contains named operations that are not mapped. Provide a calibration instance containing all necessary mappings."
            )

        self._sync_counter = 0
        self._buses = self._populate_buses()

        # Pre-processing: Update time of flight
        if times_of_flight is not None:
            for bus in self._buses.keys() & times_of_flight.keys():
                self._buses[bus].time_of_flight = times_of_flight[bus]

        # Recursive traversal to convert QProgram blocks to Sequence
        traverse(self._qprogram._body)

        # Post-processing: Add stop instructions and compile
        for bus in self._buses:
            self._buses[bus].qpy_block_stack[0].append_component(component=QPyInstructions.Stop())
            self._buses[bus].qpy_sequence._program.compile()

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        sequences = {bus: bus_info.qpy_sequence for bus, bus_info in self._buses.items()}
        acquisitions = {bus: bus_info.acquisitions for bus, bus_info in self._buses.items()}
        return sequences, acquisitions

    def _populate_buses(self):
        """Map each bus in the QProgram to a BusCompilationInfo instance.

        Returns:
            A dictionary where the keys are bus names and the values are BusCompilationInfo objects.
        """

        return {bus: BusCompilationInfo() for bus in self._qprogram.buses}

    def _append_waveform_to_bus(self, bus: str, waveform: Waveform | None, default_length: int = 0):
        _hash = QbloxCompiler._hash_waveform(waveform) if waveform else f"zeros {default_length}"

        if _hash in self._buses[bus].waveform_to_index:
            index = self._buses[bus].waveform_to_index[_hash]
            length = next(
                len(waveform.data)
                for waveform in self._buses[bus].qpy_sequence._waveforms._waveforms
                if waveform.index == index
            )
            return index, length

        envelope = waveform.envelope() if waveform else np.zeros(default_length)
        index = self._buses[bus].qpy_sequence._waveforms.add(envelope)
        self._buses[bus].waveform_to_index[_hash] = index
        return index, len(envelope)

    def _append_to_waveforms_of_bus(self, bus: str, waveform_I: Waveform, waveform_Q: Waveform | None):
        """Append waveforms to Sequence's Waveforms of the given bus.

        Args:
            bus (str): Name of the bus.
            waveform_I (Waveform): I waveform.
            waveform_Q (Waveform | None): Q waveform.
        """

        index_I, length_I = self._append_waveform_to_bus(bus, waveform_I, 0)
        index_Q, _ = self._append_waveform_to_bus(bus, waveform_Q, len(waveform_I.envelope()))
        return index_I, index_Q, length_I

    def _append_to_weights_of_bus(self, bus: str, weights: IQPair):
        def handle_waveform(waveform: Waveform):
            _hash = QbloxCompiler._hash_waveform(waveform)

            if _hash in self._buses[bus].weight_to_index:
                index = self._buses[bus].weight_to_index[_hash]
                length = next(
                    len(weight.data)
                    for weight in self._buses[bus].qpy_sequence._weights._weights  # pylint: disable=protected-access
                    if weight.index == index
                )
                return index, length

            envelope = waveform.envelope()
            length = len(envelope)
            index = self._buses[bus].qpy_sequence._weights.add(envelope)  # pylint: disable=protected-access
            self._buses[bus].weight_to_index[_hash] = index
            return index, length

        index_I, length_I = handle_waveform(weights.I)
        index_Q, _ = handle_waveform(weights.Q)
        return index_I, index_Q, length_I

    def _handle_parallel(self, element: Parallel):
        if not element.loops:
            raise NotImplementedError("Parallel block should contain loops.")
        if any(isinstance(loop, Loop) for loop in element.loops):
            raise NotImplementedError("Loops with arbitrary numpy arrays are not currently supported for QBlox.")

        loops = []
        iterations = []
        for loop in element.loops:
            start, step, iters = QbloxCompiler._convert_for_loop_values(loop)  # type: ignore[arg-type]
            loops.append((start, step))
            iterations.append(iters)
        iterations = min(iterations)

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
        info: dict[str, dict] = {
            bus: {"operations": [], "waveforms": [], "waveform_indexes": []} for bus in self._buses
        }

        operations = QbloxCompiler._get_operations_that_have_variable(element)
        waveforms = QbloxCompiler._get_waveforms_that_have_variable(element)
        weights = QbloxCompiler._get_weights_that_have_variable(element)

        for bus, operation in operations.items():
            info[bus]["operations"] = operation
        for bus, waveform in waveforms.items():
            info[bus]["waveforms"] = waveform

        print(info)

        print(operations, waveforms, weights)

        for bus, waveform_list in waveforms.items():
            info[bus]["waveform_indexes"] = []
            for waveform in waveform_list:
                indexes: list = []
                element.variable._value = element.start
                while element.variable.value <= element.stop:
                    index, length = self._append_waveform_to_bus(bus, waveform)
                    indexes.append(index)
                    print(index, length)
                    element.variable._value += element.step
                info[bus]["waveform_indexes"].append((indexes[0], 1))

        print(info)

        start, step, iterations = QbloxCompiler._convert_for_loop_values(element)

        loops: dict[str, list[tuple[int, int]]] = {}
        # Ensure all buses are in loops
        for bus in self._buses:
            loops.setdefault(bus, [])

        # Add initial values to the loops dictionary grouped by bus
        for bus in self._buses:
            loops[bus].extend(info[bus]["waveform_indexes"])

        # Initialize the loops dictionary using operations
        for bus in operations:
            loops[bus].append((start, step))

        print(loops)

        for bus in self._buses:
            qpy_loop = QPyProgram.IterativeLoop(
                name=f"loop_{self._buses[bus].loop_counter}", iterations=iterations, loops=loops[bus]
            )
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            for i, waveform in enumerate(info[bus]["waveforms"]):
                self._buses[bus].waveform_to_register[waveform] = qpy_loop.loop_registers[i]
            if info[bus]["operations"]:
                self._buses[bus].variable_to_register[element.variable] = qpy_loop.loop_registers[-1]
            self._buses[bus].loop_counter += 1

            self._buses[bus]._allocated_registers_of_block[element._uuid] = []
            self._buses[bus]._allocated_registers_of_block[element._uuid].append(qpy_loop.iteration_register)
            self._buses[bus]._allocated_registers_of_block[element._uuid].extend(qpy_loop.loop_registers)
            for register in self._buses[bus]._allocated_registers_of_block[element._uuid]:
                self._buses[bus].qpy_sequence._program._memory.allocate_register_and_mark_in_scope(register)
        return True

    def _handle_loop(self, _: Loop):
        raise NotImplementedError("Loops with arbitrary numpy arrays are not currently supported for QBlox.")

    def _handle_set_frequency(self, element: SetFrequency):
        frequency = (
            self._buses[element.bus].variable_to_register[element.frequency]
            if isinstance(element.frequency, Variable)
            else QbloxCompiler._convert_value_to_Q1ASM(element.frequency, Domain.Frequency)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetFreq(frequency=frequency)
        )

    def _handle_set_phase(self, element: SetPhase):
        phase = (
            self._buses[element.bus].variable_to_register[element.phase]
            if isinstance(element.phase, Variable)
            else QbloxCompiler._convert_value_to_Q1ASM(element.phase, Domain.Voltage)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(component=QPyInstructions.SetPh(phase=phase))

    def _handle_reset_phase(self, element: ResetPhase):
        self._buses[element.bus].qpy_block_stack[-1].append_component(component=QPyInstructions.ResetPh())

    def _handle_set_gain(self, element: SetGain):
        gain = (
            self._buses[element.bus].variable_to_register[element.gain]
            if isinstance(element.gain, Variable)
            else QbloxCompiler._convert_value_to_Q1ASM(element.gain, Domain.Voltage)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetAwgGain(gain_0=gain, gain_1=gain)
        )

    def _handle_set_offset(self, element: SetOffset):
        offset_0 = (
            self._buses[element.bus].variable_to_register[element.offset_path0]
            if isinstance(element.offset_path0, Variable)
            else QbloxCompiler._convert_value_to_Q1ASM(element.offset_path0, Domain.Voltage)
        )
        offset_1 = (
            self._buses[element.bus].variable_to_register[element.offset_path1]
            if isinstance(element.offset_path1, Variable)
            else QbloxCompiler._convert_value_to_Q1ASM(element.offset_path1, Domain.Voltage)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetAwgOffs(offset_0=offset_0, offset_1=offset_1)
        )

    def _handle_wait(self, element: Wait):
        duration: QPyProgram.Register | int
        if isinstance(element.duration, Variable):
            duration = self._buses[element.bus].variable_to_register[element.duration]
            self._buses[element.bus].dynamic_durations.append(element.duration)
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Wait(wait_time=duration)
            )
        else:
            duration = QbloxCompiler._convert_value_to_Q1ASM(element.duration, Domain.Time)
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

    def _handle_sync(self, element: Sync):
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
            self.__handle_static_sync(buses=buses)

        # In any case, mark al buses as synced.
        for bus in buses:
            self._buses[bus].marked_for_sync = False

    def __handle_static_sync(self, buses: set[str]):
        max_duration = max(self._buses[bus].static_duration for bus in buses)
        for bus in buses:
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
        self._buses[element.bus].acquisitions[acquisition_name] = AcquisitionData(save_adc=element.save_adc)

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
            self._buses[element.bus].qpy_sequence._program._memory.allocate_register_and_mark_in_scope(bin_register)
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
            self._buses[element.bus].qpy_sequence._program._memory.allocate_register_and_mark_in_scope(register_I)
            self._buses[element.bus].qpy_sequence._program._memory.allocate_register_and_mark_in_scope(register_Q)
        self._buses[element.bus].static_duration += integration_length
        self._buses[element.bus].next_bin_index = 0  # maybe this counter can be removed completely
        self._buses[element.bus].next_acquisition_index += 1
        self._buses[element.bus].marked_for_sync = True

    def _handle_play(self, element: Play):
        waveform_I, waveform_Q = element.get_waveforms()
        waveform_variables = element.get_waveform_variables()
        if any(variable.domain is Domain.Time for variable in waveform_variables):
            raise RuntimeError("No dynamic durations are allowed in Qblox.")
        duration = waveform_I.get_duration()
        if not waveform_variables:
            index_I, index_Q, duration = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
        else:
            if waveform_I in self._buses[element.bus].waveform_to_register:
                index_I = self._buses[element.bus].waveform_to_register[waveform_I]
            else:
                index_I, duration = self._append_waveform_to_bus(element.bus, waveform_I)
                register_I = QPyProgram.Register()
                self._buses[element.bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Move(var=index_I, register=register_I)
                )
                self._buses[element.bus].qpy_sequence._program._memory.allocate_register_and_mark_in_scope(register_I)
                index_I = register_I
            if waveform_Q in self._buses[element.bus].waveform_to_register:
                index_Q = self._buses[element.bus].waveform_to_register[waveform_Q]
            else:
                index_Q, duration = self._append_waveform_to_bus(element.bus, waveform_Q)
                register_Q = QPyProgram.Register()
                self._buses[element.bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Move(var=index_Q, register=register_Q)
                )
                self._buses[element.bus].qpy_sequence._program._memory.allocate_register_and_mark_in_scope(register_Q)
                index_Q = register_Q

        if element.wait_time is not None:
            duration = element.wait_time

        duration = QbloxCompiler._convert_value_to_Q1ASM(duration, Domain.Time)
        self._buses[element.bus].static_duration += duration
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.Play(index_I, index_Q, wait_time=duration)
        )
        self._buses[element.bus].marked_for_sync = True

    @staticmethod
    def _get_operations_that_have_variable(loop: ForLoop, starting_block: Block | None = None):
        def collect_operations(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_operations(element)
                else:
                    if any(variable == loop.variable for variable in element.get_variables()):
                        yield getattr(element, "bus"), type(element)

        starting_block = starting_block or loop
        bus_and_operation_tuples = set(collect_operations(starting_block))

        operations: dict[str, list] = {}
        for bus, operation in bus_and_operation_tuples:
            operations.setdefault(bus, []).append(operation)

        print(operations)

        return operations

    @staticmethod
    def _get_waveforms_that_have_variable(loop: ForLoop, starting_block: Block | None = None):
        def collect_waveforms(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_waveforms(element)
                else:
                    if isinstance(element, (Play, Measure)):
                        waveform_I, waveform_Q = element.get_waveforms()
                        if loop.variable in waveform_I.get_variables():
                            yield element.bus, waveform_I
                        if waveform_Q and loop.variable in waveform_Q.get_variables():
                            yield element.bus, waveform_Q

        starting_block = starting_block or loop
        bus_and_waveforms_tuples = set(collect_waveforms(starting_block))

        waveforms: dict[str, list] = {}
        for bus, waveform in bus_and_waveforms_tuples:
            waveforms.setdefault(bus, []).append(waveform)

        print(waveforms)

        return waveforms

    @staticmethod
    def _get_weights_that_have_variable(loop: ForLoop, starting_block: Block | None = None):
        def collect_weights(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_weights(element)
                else:
                    if isinstance(element, (Acquire, Measure)):
                        weight_I, weight_Q = element.get_weights()
                        if loop.variable in weight_I.get_variables():
                            yield weight_I
                        if loop.variable in weight_Q.get_variables():
                            yield weight_Q

        starting_block = starting_block or loop
        weights = set(collect_weights(starting_block))

        print(weights)

        return weights

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
    def _convert_for_loop_values(for_loop: ForLoop):
        iterations = QbloxCompiler._calculate_iterations(start=for_loop.start, stop=for_loop.stop, step=for_loop.step)
        qblox_start = QbloxCompiler._convert_value_to_Q1ASM(for_loop.start, for_loop.variable.domain)
        qblox_stop = QbloxCompiler._convert_value_to_Q1ASM(for_loop.stop, for_loop.variable.domain)
        qblox_step = (qblox_stop - qblox_start) // (iterations - 1)
        return (qblox_start, qblox_step, iterations)

    @staticmethod
    def _convert_value_to_Q1ASM(value: int | float, domain: Domain) -> int:
        conversion_map: dict[Domain, Callable[[Any], int]] = {
            Domain.Frequency: lambda x: int(x * QbloxCompiler.FREQUENCY_COEFF),
            Domain.Phase: lambda x: int(x * QbloxCompiler.PHASE_COEFF),
            Domain.Voltage: lambda x: int(x * QbloxCompiler.VOLTAGE_COEFF),
            Domain.Time: lambda x: int(max(x, QbloxCompiler.MINIMUM_TIME)),
        }
        convert_func = conversion_map.get(domain, lambda x: int(x))  # pylint: disable=unnecessary-lambda
        return convert_func(value)

    @staticmethod
    def _hash_waveform(waveform: Waveform):
        hashes = {
            key: (value.__dict__ if isinstance(value, Waveform) else value) for key, value in waveform.__dict__.items()
        }
        return f"{waveform.__class__.__name__} {hashes}"
