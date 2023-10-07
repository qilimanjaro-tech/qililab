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
from typing import Any, Callable

import numpy as np
import qpysequence as QPy
import qpysequence.program as QPyProgram
import qpysequence.program.instructions as QPyInstructions

from qililab.qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qililab.qprogram.operations import (
    Acquire,
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
from qililab.qprogram.variable import Variable
from qililab.waveforms import IQPair, Waveform


class BusCompilationInfo:  # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Class representing the information stored by QBloxCompiler for a bus."""

    def __init__(self):
        # The generated Sequence
        self.qpy_sequence = QPy.Sequence(
            program=QPy.Program(), waveforms=QPy.Waveforms(), acquisitions=QPy.Acquisitions(), weights=QPy.Weights()
        )

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

        # Syncing durations
        self.static_duration = 0
        self.dynamic_durations: list[Variable] = []
        self.sync_durations: list[QPyProgram.Register] = []

        # Syncing marker. If true, a real-time instruction has been added since the last sync or the beginning of the program.
        self.marked_for_sync = False


class QbloxCompiler:  # pylint: disable=too-few-public-methods
    """A class for compiling QProgram to QBlox hardware."""

    minimum_wait_duration: int = 4

    def __init__(self):
        # Handlers to map each operation to a corresponding handler function
        self._handlers: dict[type, Callable] = {
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
            Acquire: self._handle_acquire,
            Play: self._handle_play,
        }

        self._qprogram: QProgram
        self._buses: dict[str, BusCompilationInfo]
        self._sync_counter: int = 0

    def compile(self, qprogram: QProgram) -> dict[str, QPy.Sequence]:
        """Compile QProgram to qpysequence.Sequence

        Args:
            qprogram (QProgram): The QProgram to be compiled

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
                    if isinstance(element, (ForLoop, Parallel, Loop, Average)):
                        self._handle_sync(element=Sync(buses=None))
                    if appended:
                        for bus in self._buses:
                            self._buses[bus].qpy_block_stack.pop()
            for bus in self._buses:
                self._buses[bus].qprogram_block_stack.pop()

        self._qprogram = qprogram
        self._buses = self._populate_buses()

        # Recursive traversal to convert QProgram blocks to Sequence
        traverse(self._qprogram._program)

        # Post-processing: Add stop instructions and compile
        for bus in self._buses:
            self._buses[bus].qpy_block_stack[0].append_component(component=QPyInstructions.Stop())
            self._buses[bus].qpy_sequence._program.compile()

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        return {bus: bus_info.qpy_sequence for bus, bus_info in self._buses.items()}

    def _populate_buses(self):
        """Map each bus in the QProgram to a BusInfo instance.

        Returns:
            A dictionary where the keys are bus names and the values are BusInfo objects.
        """

        def collect_buses(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_buses(element)
                if isinstance(element, Operation):
                    bus = getattr(element, "bus", None)
                    if bus:
                        yield bus

        buses = set(collect_buses(self._qprogram._program))
        return {bus: BusCompilationInfo() for bus in buses}

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

            envelope = waveform.envelope() if waveform else np.zeros(default_length)
            index = self._buses[bus].qpy_sequence._waveforms.add(envelope)
            self._buses[bus].waveform_to_index[_hash] = index
            return index, len(envelope)

        index_I, length_I = handle_waveform(waveform_I, 0)
        index_Q, length_Q = handle_waveform(waveform_Q, len(waveform_I.envelope()))
        if length_I != length_Q:
            raise NotImplementedError("Waveforms should have equal lengths.")
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
        index_Q, length_Q = handle_waveform(weights.Q)
        if length_I != length_Q:
            raise NotImplementedError("Weights should have equal lengths.")
        return index_I, index_Q, length_I

    def _handle_parallel(self, element: Parallel):
        if not element.loops:
            raise NotImplementedError("Parallel block should contain loops.")

        loops = []
        iterations = []
        for loop in element.loops:
            operation = QbloxCompiler._get_reference_operation_of_loop(loop=loop, starting_block=element)
            if not operation:
                raise NotImplementedError("Variables referenced in loops should be used in at least one operation.")
            start, step, iters = QbloxCompiler._convert_for_loop_values(loop, operation)
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

    def _handle_for_loop(self, element: ForLoop):
        operation = QbloxCompiler._get_reference_operation_of_loop(element)
        if not operation:
            raise NotImplementedError("Variables referenced in loops should be used in at least one operation.")
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

    def _handle_loop(self, element: Loop):
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
        gain_0 = (
            self._buses[element.bus].variable_to_register[element.gain_path0]
            if isinstance(element.gain_path0, Variable)
            else convert(element.gain_path0)
        )
        gain_1 = (
            self._buses[element.bus].variable_to_register[element.gain_path1]
            if isinstance(element.gain_path1, Variable)
            else convert(element.gain_path1)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetAwgGain(gain_0=gain_0, gain_1=gain_1)
        )

    def _handle_set_offset(self, element: SetOffset):
        convert = QbloxCompiler._convert_value(element)
        offset_0 = (
            self._buses[element.bus].variable_to_register[element.offset_path0]
            if isinstance(element.offset_path0, Variable)
            else convert(element.offset_path0)
        )
        offset_1 = (
            self._buses[element.bus].variable_to_register[element.offset_path1]
            if isinstance(element.offset_path1, Variable)
            else convert(element.offset_path1)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.SetAwgOffs(offset_0=offset_0, offset_1=offset_1)
        )

    def _handle_wait(self, element: Wait):
        duration: QPyProgram.Register | int
        if isinstance(element.duration, Variable):
            duration = self._buses[element.bus].variable_to_register[element.duration]
            self._buses[element.bus].dynamic_durations.append(element.duration)
        else:
            convert = QbloxCompiler._convert_value(element)
            duration = convert(element.duration)
            self._buses[element.bus].static_duration += duration
        self._buses[element.bus].qpy_block_stack[-1].append_component(
            component=QPyInstructions.Wait(wait_time=duration)
        )
        self._buses[element.bus].marked_for_sync = True

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
                self._buses[bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Wait(wait_time=duration_diff)
                )
                self._buses[bus].static_duration += duration_diff

    def __handle_dynamic_sync(self, buses: set[str]):
        sync_duration_to_be_added: dict[str, QPyProgram.Register] = {}
        for bus in buses:
            # Create seperate block for readability.
            sync_block_label = f"sync{self._sync_counter}_start"
            sync_block = QPyProgram.Block(name=sync_block_label)
            self._buses[bus].qpy_sequence._program.append_block(sync_block)

            # Create register to hold the syncing difference.
            sync_register = QPyProgram.Register()
            # Initialize register with static duration of bus.
            sync_block.append_component(
                component=QPyInstructions.Move(var=self._buses[bus].static_duration, register=sync_register)
            )
            # Add dynamic durations of bus, if any.
            for dynamic_duration in self._buses[bus].dynamic_durations:
                dynamic_duration_register = self._buses[bus].variable_to_register[dynamic_duration]
                sync_block.append_component(
                    component=QPyInstructions.Add(
                        origin=sync_register, var=dynamic_duration_register, destination=sync_register
                    )
                )
                sync_block.append_component(component=QPyInstructions.Nop())
            # Add durations created by previous syncs, if any.
            for i, sync_duration in enumerate(self._buses[bus].sync_durations):
                # For every previous sync, we add its register if the register is positive.
                # So we jump to next instruction, if register is negative.
                skip_previous_sync_label = f"sync{self._sync_counter}_self{i}"
                sync_block.append_component(
                    component=QPyInstructions.Jlt(
                        a=sync_duration,
                        b=QbloxCompiler.minimum_wait_duration - 1,
                        instr=f"@{skip_previous_sync_label}",
                    )
                )
                sync_block.append_component(
                    component=QPyInstructions.Add(origin=sync_register, var=sync_duration, destination=sync_register)
                )
                sync_block.append_component(component=QPyInstructions.Nop().with_label(skip_previous_sync_label))

            # Invert the register (x => -x)
            sync_block.append_component(component=QPyInstructions.Not(var=sync_register, register=sync_register))
            sync_block.append_component(
                component=QPyInstructions.Add(origin=sync_register, var=1, destination=sync_register)
            )

            # Get the other buses involved in sync operation, that is except the current one.
            other_buses = set(other_bus for other_bus in buses if other_bus != bus)

            # Find the maximum static duration of other buses.
            max_static_duration = max(self._buses[other_bus].static_duration for other_bus in other_buses)

            # Add static duration
            sync_block.append_component(
                component=QPyInstructions.Add(origin=sync_register, var=max_static_duration, destination=sync_register)
            )

            # Add dynamic durations, if any.
            other_dynamic_durations = set(
                other_dynamic_duration
                for other_bus in other_buses
                for other_dynamic_duration in self._buses[other_bus].dynamic_durations
            )
            if len(other_dynamic_durations) > 1:
                # In order to support this, we would have to find the maximum of the registers.
                raise NotImplementedError(
                    "Sync operations when multiple dynamic durations are present is not supported yet."
                )
            elif len(other_dynamic_durations) == 1:
                other_dynamic_duration = next(iter(other_dynamic_durations))
                max_repetitions = max(len(self._buses[bus].dynamic_durations) for bus in other_buses)
                dynamic_duration_register = self._buses[bus].variable_to_register[other_dynamic_duration]
                for _ in range(max_repetitions):
                    sync_block.append_component(
                        component=QPyInstructions.Add(
                            origin=sync_register, var=dynamic_duration_register, destination=sync_register
                        )
                    )
                    sync_block.append_component(component=QPyInstructions.Nop())
            # TODO: Review this again. It currently adds a register from another sequence!
            # Add durations created by previous syncs, if any.
            # for i, sync_duration in enumerate(self._buses[other_bus].sync_durations):
            #     # For every previous sync, we add its register if the register is positive.
            #     # So we jump to next instruction, if register is negative.
            #     skip_previous_sync_label = f"sync{self._sync_counter}_other{i}"
            #     sync_block.append_component(
            #         component=QPyInstructions.Jlt(a=sync_duration, b=QbloxCompiler.minimum_wait_duration - 1, instr=f"@{skip_previous_sync_label}")
            #     )
            #     sync_block.append_component(
            #         component=QPyInstructions.Add(
            #             origin=sync_register, var=sync_duration, destination=sync_register
            #         )
            #     )
            #     sync_block.append_component(component=QPyInstructions.Nop().with_label(skip_previous_sync_label))

            # sync_register now holds the difference of the two buses.
            # If sync_register > 0, then `bus` is behind, otherwise `other_bus` is behind.
            # If `other_bus` is behind, skip wait instruction. Else, wait.
            skip_sync_label = f"sync{self._sync_counter}_skip"
            sync_block.append_component(
                component=QPyInstructions.Jlt(
                    a=sync_register, b=QbloxCompiler.minimum_wait_duration - 1, instr=f"@{skip_sync_label}"
                )
            )
            sync_block.append_component(component=QPyInstructions.Wait(wait_time=sync_register))
            sync_block.append_component(component=QPyInstructions.Nop().with_label(skip_sync_label))

            # Jump back to main flow.
            end_sync_label = f"sync{self._sync_counter}_end"
            sync_block.append_component(component=QPyInstructions.Jmp(instr=f"@{end_sync_label}"))

            # Append the block to program and jump to it.
            self._buses[bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Jmp(instr=f"@{sync_block_label}")
            )
            self._buses[bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Nop().with_label(end_sync_label)
            )

            # Mark sync_register to be added to sync_durations.
            sync_duration_to_be_added[bus] = sync_register
        for bus in sync_duration_to_be_added:
            self._buses[bus].sync_durations.append(sync_duration_to_be_added[bus])
        # Increate global sync counter
        self._sync_counter += 1

    def _handle_acquire(self, element: Acquire):
        loops = [
            (i, loop)
            for i, loop in enumerate(self._buses[element.bus].qpy_block_stack)
            if isinstance(loop, QPyProgram.Loop) and not loop.name.startswith("avg")
        ]
        num_bins = math.prod(loop[1]._iterations for loop in loops)
        self._buses[element.bus].qpy_sequence._acquisitions.add(
            name=f"acquisition_{self._buses[element.bus].next_acquisition_index}",
            num_bins=num_bins,
            index=self._buses[element.bus].next_acquisition_index,
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
        if not waveform_variables:
            index_I, index_Q, wf_duration = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
            if element.duration is not None and isinstance(element.duration, Variable):
                duration = self._buses[element.bus].variable_to_register[element.duration]
                self._buses[element.bus].static_duration += QbloxCompiler.minimum_wait_duration
                self._buses[element.bus].dynamic_durations.append(element.duration)
                self._buses[element.bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Play(index_I, index_Q, wait_time=QbloxCompiler.minimum_wait_duration)
                )
                self._buses[element.bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Wait(wait_time=duration)
                )
            else:
                convert = QbloxCompiler._convert_value(element)
                duration = element.duration if element.duration is not None else wf_duration
                duration = convert(duration)
                self._buses[element.bus].static_duration += duration
                self._buses[element.bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Play(index_I, index_Q, wait_time=duration)
                )
            self._buses[element.bus].marked_for_sync = True

    @staticmethod
    def _get_reference_operation_of_loop(loop: ForLoop, starting_block: Block | None = None):
        def collect_operations(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_operations(element)
                else:
                    if any(variable is loop.variable for variable in element.get_variables()):
                        yield element

        starting_block = starting_block or loop
        operations = list(collect_operations(starting_block))

        if not operations:
            return None
        if len(set(map(type, operations))) != 1:
            raise NotImplementedError("Variables referenced in a loop cannot be used in different types of operations.")
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
        else:
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
            SetPhase: lambda x: int(x * 1e9 / 360),
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
