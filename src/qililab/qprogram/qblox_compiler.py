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
from typing import Callable

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


class BusInfo:  # pylint: disable=too-many-instance-attributes, too-few-public-methods
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


class QbloxCompiler:  # pylint: disable=too-few-public-methods
    """A class for compiling QProgram to QBlox hardware."""

    minimum_wait_duration: int = 4

    def __init__(self, integration_length: int = 1000):
        # External settings
        self._integration_length = integration_length

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
        self._buses: dict[str, BusInfo]

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
        return {bus: BusInfo() for bus in buses}

    def _append_to_waveforms_of_bus(self, bus: str, waveform_I: Waveform, waveform_Q: Waveform | None):
        """Append waveforms to Sequence's Waveforms of the given bus.

        Args:
            bus (str): Name of the bus.
            waveform_I (Waveform): I waveform.
            waveform_Q (Waveform | None): Q waveform.
        """

        def handle_waveform(waveform: Waveform | None, default_length: int = 0):
            _hash = QbloxCompiler._hash(waveform) if waveform else f"zeros {default_length}"

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
            _hash = QbloxCompiler._hash(waveform)

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
        if len({int((loop.stop - loop.start) / loop.step) for loop in element.loops}) != 1:
            raise NotImplementedError("Loops run in parallel should have the same number of iterations.")
        for bus in self._buses:
            iterations = int((element.loops[0].stop - element.loops[0].start) / element.loops[0].step)
            qpy_loop = QPyProgram.Loop(name=f"loop_{self._buses[bus].loop_counter}", begin=iterations)
            for loop in element.loops:
                operation = QbloxCompiler._get_reference_operation_of_loop(loop=loop, starting_block=element)
                if not operation:
                    raise NotImplementedError("Variables referenced in loops should be used in at least one operation.")
                begin, _, step = QbloxCompiler._convert_for_loop_values(loop, operation)
                loop_register = QPyProgram.Register()
                self._buses[bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Move(var=begin, register=loop_register)
                )
                qpy_loop.builtin_components.insert(
                    0,
                    QPyInstructions.Add(loop_register, step, loop_register)
                    if step > 0
                    else QPyInstructions.Sub(loop_register, step, loop_register),
                )
                self._buses[bus].variable_to_register[loop.variable] = loop_register
            qpy_loop.append_component(QPyInstructions.WaitSync(4))
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].loop_counter += 1
        return True

    def _handle_average(self, element: Average):
        for bus in self._buses:
            qpy_loop = QPyProgram.Loop(name=f"avg_{self._buses[bus].average_counter}", begin=element.shots)
            qpy_loop.append_component(
                component=QPyInstructions.WaitSync(wait_time=QbloxCompiler.minimum_wait_duration),
                bot_position=len(qpy_loop.components),
            )
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].average_counter += 1
        return True

    def _handle_for_loop(self, element: ForLoop):
        operation = QbloxCompiler._get_reference_operation_of_loop(element)
        if not operation:
            raise NotImplementedError("Variables referenced in loops should be used in at least one operation.")
        begin, end, step = QbloxCompiler._convert_for_loop_values(element, operation)
        for bus in self._buses:
            qpy_loop = QPyProgram.Loop(name=f"loop_{self._buses[bus].loop_counter}", begin=begin, end=end, step=step)
            qpy_loop.append_component(
                component=QPyInstructions.WaitSync(wait_time=QbloxCompiler.minimum_wait_duration),
                bot_position=len(qpy_loop.components),
            )
            self._buses[bus].qpy_block_stack[-1].append_component(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].variable_to_register[element.variable] = qpy_loop.counter_register
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
            component=QPyInstructions.SetAwgOffs(gain_0=offset_0, gain_1=offset_1)
        )

    def _handle_wait(self, element: Wait):
        convert = QbloxCompiler._convert_value(element)
        time = (
            self._buses[element.bus].variable_to_register[element.time]
            if isinstance(element.time, Variable)
            else convert(element.time)
        )
        self._buses[element.bus].qpy_block_stack[-1].append_component(component=QPyInstructions.Wait(wait_time=time))

    def _handle_sync(self, _: Sync):
        # QBlox does not currently support syncing on selective sequences. If it did we would do somethin like:
        # buses = element.buses if element.buses is not None else self._buses.keys()
        for bus in self._buses:
            self._buses[bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.WaitSync(wait_time=QbloxCompiler.minimum_wait_duration)
            )

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

        if element.weights:
            index_I, index_Q, integration_length = self._append_to_weights_of_bus(element.bus, weights=element.weights)

        if num_bins > 1:
            bin_register = QPyProgram.Register()
            block_index_for_move_instruction = loops[0][0] - 1 if loops else -2
            block_index_for_add_instruction = loops[-1][0] if loops else -1
            self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].append_component(
                component=QPyInstructions.Move(var=self._buses[element.bus].next_bin_index, register=bin_register),
                bot_position=len(self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].components),
            )
            if element.weights:
                register_I, register_Q = QPyProgram.Register(), QPyProgram.Register()
                self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].append_component(
                    component=QPyInstructions.Move(var=index_I, register=register_I),
                    bot_position=len(
                        self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].components
                    ),
                )
                self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].append_component(
                    component=QPyInstructions.Move(var=index_Q, register=register_Q),
                    bot_position=len(
                        self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].components
                    ),
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
            else:
                self._buses[element.bus].qpy_block_stack[-1].append_component(
                    component=QPyInstructions.Acquire(
                        acq_index=self._buses[element.bus].next_acquisition_index,
                        bin_index=bin_register,
                        wait_time=self._integration_length,
                    )
                )
            self._buses[element.bus].qpy_block_stack[block_index_for_add_instruction].append_component(
                component=QPyInstructions.Add(origin=bin_register, var=1, destination=bin_register)
            )
        elif element.weights:
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
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Acquire(
                    acq_index=self._buses[element.bus].next_acquisition_index,
                    bin_index=self._buses[element.bus].next_bin_index,
                    wait_time=self._integration_length,
                )
            )
        self._buses[element.bus].next_bin_index += num_bins
        self._buses[element.bus].next_acquisition_index += 1

    def _handle_play(self, element: Play):
        waveform_I, waveform_Q = element.get_waveforms()
        variables = element.get_variables()
        if not variables:
            index_I, index_Q, length = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
            self._buses[element.bus].qpy_block_stack[-1].append_component(
                component=QPyInstructions.Play(index_I, index_Q, wait_time=length)
            )

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
        if isinstance(operations[0], Play):
            raise NotImplementedError("TODO: Variables referenced in a loop cannot be used in Play operation.")
        return operations[0]

    @staticmethod
    def _convert_for_loop_values(for_loop: ForLoop, operation: Operation):
        convert = QbloxCompiler._convert_value(operation)
        return tuple(convert(value) for value in (for_loop.start, for_loop.stop, for_loop.step))

    @staticmethod
    def _convert_value(operation: Operation):
        conversion_map = {
            SetFrequency: lambda x: int(x * 4),
            SetPhase: lambda x: int(x * 1e9 / 360),
            SetGain: lambda x: int(x * 32_767),
            SetOffset: lambda x: int(x * 32_767),
            Wait: lambda x: max(x, QbloxCompiler.minimum_wait_duration),
        }
        return conversion_map.get(type(operation), lambda x: x)

    @staticmethod
    def _hash(waveform: Waveform):
        hashes = {
            key: (value.__dict__ if isinstance(value, Waveform) else value) for key, value in waveform.__dict__.items()
        }
        return f"{waveform.__class__.__name__} {hashes}"
