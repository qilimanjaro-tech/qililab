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

from collections import deque

import numpy as np

from qililab.qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qililab.qprogram.operations import (
    Acquire,
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.variable import FloatVariable, IntVariable, Variable
from qililab.waveforms import IQPair, Waveform


class QProgram:
    """A class for building quantum programs.

    This class provides an interface for building quantum programs,
    including defining operations, managing variables, and handling blocks.
    It contains methods for creating, manipulating and controlling
    the execution flow of quantum operations within a program.

    Attributes:
        _program (Block): The main program block.
        _variables (list[Variable]): List of variables used within the program.
        _block_stack (deque[Block]): A stack to manage nested blocks within the program.

    Examples:

        The following example illustrates how to define a Rabi sequence using QProgram.

        .. code-block:: python3

            qp = QProgram()
            amplitude = qp.variable(float)
            drag = DRAG(amplitude=amplitude, duration=40, num_sigmas=4, drag_correction=1.2)
            square_wf = Square(amplitude=1.0, duration=1000)
            zeros_wf = Square(amplitude=0.0, duration=1000)
            with qp.loop(variable=amplitude, values=np.arange(0, 1, 101)):
                qp.play(bus="drive", waveform=drag)
                qp.sync()
                qp.play(bus="readout", waveform=IQPair(I=square_wf, Q=zeros_wf))
                qp.acquire(bus="readout")
    """

    def __init__(self):
        self._program: Block = Block()
        self._variables: list[Variable] = []
        self._block_stack: deque[Block] = deque([self._program])

    def _append_to_block_stack(self, block: Block):
        self._block_stack.append(block)

    def _pop_from_block_stack(self):
        return self._block_stack.pop()

    @property
    def _active_block(self) -> Block:
        return self._block_stack[-1]

    def block(self):
        """Define a generic block for scoping operations.

        Blocks need to open a scope.

        Returns:
            Block: The block.

        Examples:

            >>> with qp.block() as block:
            >>>    # operations that shall be executed in the block
        """
        return QProgram._BlockContext(qprogram=self)

    def parallel(self, loops: list[ForLoop]):
        """Define a block for running multiple loops in parallel.

        Blocks need to open a scope.

        Examples:
            >>> gain = qp.variable(float)
            >>> frequency = qp.variable(float)
            >>> with qp.parallel(loops=[ForLoop(variable=frequency, start=0, stop=100, step=10),
                                        ForLoop(variable=gain, start=0.0, stop=1.0, step=0.1)]):
            >>>    # operations that shall be executed in the block

        Args:
            loops (list[Loop  |  ForLoop]): The loops to run in parallel

        Returns:
            Parallel: The parallel block.
        """
        return QProgram._ParallelContext(qprogram=self, loops=loops)

    def average(self, shots: int):
        """Define an acquire loop block with averaging in real time.

        Blocks need to open a scope.

        Args:
            iterations (int): The number of acquire iterations.

        Returns:
            AcquireLoop: The acquire_loop block.

        Examples:

            >>> with qp.acquire_loop(iterations=1000):
            >>>    # operations that shall be executed in the acquire_loop block
        """
        return QProgram._AverageContext(qprogram=self, iterations=shots)

    def loop(self, variable: Variable, values: np.ndarray):
        """Define a loop block to iterate values over a variable.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            values (np.ndarray): The values to iterate over.

        Returns:
            Loop: The loop block.

        Examples:

            >>> variable = qp.variable(int)
            >>> with qp.loop(variable=variable, values=np.array(range(100))):
            >>>    # operations that shall be executed in the loop block
        """

        return QProgram._LoopContext(qprogram=self, variable=variable, values=values)

    def for_loop(self, variable: Variable, start: int | float, stop: int | float, step: int | float = 1):
        """Define a for_loop block to iterate values over a variable.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            start (int | float): The start value.
            stop (int | float): The stop value.
            step (int | float, optional): The step value. Defaults to 1.

        Returns:
            Loop: The loop block.

        Examples:

            >>> variable = qp.variable(int)
            >>> with qp.for_loop(variable=variable, start=0, stop=100, step=5)):
            >>>    # operations that shall be executed in the for_loop block
        """

        return QProgram._ForLoopContext(qprogram=self, variable=variable, start=start, stop=stop, step=step)

    def play(self, bus: str, waveform: Waveform | IQPair):
        """Play a single waveform or an I/Q pair of waveforms on the bus.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (Waveform | IQPair): A single waveform or an I/Q pair of waveforms
        """
        operation = Play(bus=bus, waveform=waveform)
        self._active_block.append(operation)

    def wait(self, bus: str, time: int):
        """Adds a delay on the bus with a specified time.

        Args:
            bus (str): Unique identifier of the bus.
            time (int): Duration of the delay.
        """
        operation = Wait(bus=bus, time=time)
        self._active_block.append(operation)

    def acquire(self, bus: str, weights: IQPair | None = None):
        """Acquire results.

        Args:
            bus (str): Unique identifier of the bus.
            weights (IQPair | None, optional): Weights used during acquisition. Defaults to None.
        """
        operation = Acquire(bus=bus, weights=weights)
        self._active_block.append(operation)

    def sync(self, buses: list[str] | None = None):
        """Synchronize operations between buses, so the operations following will start at the same time. If no buses are given, then the synchronization will involve all buses present in the QProgram.

        Args:
            buses (list[str] | None, optional): List of unique identifiers of the buses. Defaults to None.
        """
        operation = Sync(buses=buses)
        self._active_block.append(operation)

    def reset_phase(self, bus: str):
        """Reset the absolute phase of the NCO associated with the bus.

        Args:
            bus (str): Unique identifier of the bus.
        """
        operation = ResetPhase(bus=bus)
        self._active_block.append(operation)

    def set_phase(self, bus: str, phase: float):
        """Set the absolute phase of the NCO associated with the bus.

        Args:
            bus (str): Unique identifier of the bus.
            phase (float): The new absolute phase of the NCO.
        """
        operation = SetPhase(bus=bus, phase=phase)
        self._active_block.append(operation)

    def set_frequency(self, bus: str, frequency: float):
        """Set the frequency of the NCO associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            frequency (float): The new frequency of the NCO.
        """
        operation = SetFrequency(bus=bus, frequency=frequency)
        self._active_block.append(operation)

    def set_gain(self, bus: str, gain_path0: float, gain_path1: float):
        """Set the gain of the AWG associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            gain_path0 (float): The new gain of the AWG for path0.
            gain_path1 (float): The new gain of the AWG for path1.
        """
        operation = SetGain(bus=bus, gain_path0=gain_path0, gain_path1=gain_path1)
        self._active_block.append(operation)

    def set_offset(self, bus: str, offset_path0: float, offset_path1: float):
        """Set the gain of the AWG associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            offset_path0 (float): The new offset of the AWG for path0.
            offset_path1 (float): The new offset of the AWG for path1.
        """
        operation = SetOffset(bus=bus, offset_path0=offset_path0, offset_path1=offset_path1)
        self._active_block.append(operation)

    def variable(self, type: type[int | float]):  # pylint: disable=redefined-builtin
        """Declare a variable.

        Args:
            type (int | float): The type of the variable.

        Raises:
            NotImplementedError: If an unsupported type is provided.

        Returns:
            IntVariable | FloatVariable: The variable.
        """

        def _int_variable(value: int = 0) -> IntVariable:
            variable = IntVariable(value)
            self._variables.append(variable)
            return variable

        def _float_variable(value: float = 0.0) -> FloatVariable:
            variable = FloatVariable(value)
            self._variables.append(variable)
            return variable

        if type == int:
            return _int_variable()
        if type == float:
            return _float_variable()
        raise NotImplementedError

    class _BlockContext:
        def __init__(self, qprogram: "QProgram"):
            self.qprogram = qprogram
            self.block: Block = Block()

        def __enter__(self):
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block

        def __exit__(self, exc_type, exc_value, exc_tb):
            block = self.qprogram._pop_from_block_stack()
            self.qprogram._active_block.append(block)

    class _ParallelContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram", loops: list[ForLoop]):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: Parallel = Parallel(loops=loops)

        def __enter__(self) -> Parallel:
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block

    class _LoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(  # pylint: disable=super-init-not-called
            self, qprogram: "QProgram", variable: Variable, values: np.ndarray
        ):
            self.qprogram = qprogram
            self.block: Loop = Loop(variable=variable, values=values)

        def __enter__(self) -> Loop:
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block

    class _ForLoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(  # pylint: disable=super-init-not-called
            self, qprogram: "QProgram", variable: Variable, start: int | float, stop: int | float, step: int | float
        ):
            self.qprogram = qprogram
            self.block: ForLoop = ForLoop(variable=variable, start=start, stop=stop, step=step)

        def __enter__(self) -> ForLoop:
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block

    class _AverageContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram", iterations: int):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: Average = Average(shots=iterations)

        def __enter__(self) -> Average:
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block
