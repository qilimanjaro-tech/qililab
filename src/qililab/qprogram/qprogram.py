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

from qililab.qprogram.blocks import Average, Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.decorators import requires_domain
from qililab.qprogram.operations import (
    Acquire,
    Measure,
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.variable import Domain, FloatVariable, IntVariable, ValueSource, Variable
from qililab.utils import DictSerializable
from qililab.waveforms import IQPair, Waveform


class QProgram(DictSerializable):
    """QProgram is a hardware-agnostic pulse-level programming interface for describing quantum programs.

    This class provides an interface for building quantum programs,
    including defining operations, managing variables, and handling blocks.
    It contains methods for creating, manipulating and controlling
    the execution flow of quantum operations within a program.

    Attributes:
        disable_autosync (bool): If set to True, then loop iterations are not automatically synced.

    Examples:

        The following example illustrates how to define a Rabi sequence using QProgram.

        .. code-block:: python3

            from qililab import QProgram, Domain, IQPair, Square

            qp = QProgram()

            # Pulse used for changing the state of qubit
            control_wf = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4.0, drag_correction=-2.5)

            # Pulse used for exciting the resonator for readout
            readout_wf = IQPair(I=Square(amplitude=1.0, duration=400), Q=Square(amplitude=0.0, duration=400))

            # Weights used during integration
            weights = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=1.0, duration=2000))

            # Declare a variable
            gain = qp.variable(Domain.Voltage)

            # Loop the variable's value over the range [0.0, 1.0]
            with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.01):
                # Change the gain output of the drive_bus
                qp.set_gain(bus="drive_bus", gain=gain)

                # Play the control pulse
                qp.play(bus="drive_bus", waveform=control_wf)

                # Sync the buses
                qp.sync()

                # Play the readout pulse
                qp.play(bus="readout_bus", waveform=readout_wf, wait_time=120)

                # Acquire results
                qp.acquire(bus="readout_bus", weights=weights)

    """

    def __init__(self, disable_autosync: bool = False) -> None:
        self.disable_autosync: bool = disable_autosync

        self._body: Block = Block()
        self._buses: set[str] = set()
        self._variables: list[Variable] = []
        self._block_stack: deque[Block] = deque([self._body])

    def _append_to_block_stack(self, block: Block):
        self._block_stack.append(block)

    def _pop_from_block_stack(self):
        return self._block_stack.pop()

    @property
    def body(self) -> Block:
        """Get the body of the QProgram

        Returns:
            Block: The block of the body
        """
        return self._body

    @property
    def buses(self) -> set[str]:
        """Get the buses of the QProgram

        Returns:
            set[str]: A set of the names of the buses
        """
        return self._buses

    @property
    def variables(self) -> list[Variable]:
        """Get the variables

        Returns:
            list[Variable]: A list of variables
        """
        return self._variables

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

    def parallel(self, loops: list[Loop | ForLoop]):
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
        return QProgram._AverageContext(qprogram=self, shots=shots)

    def infinite_loop(self):
        """Define an infinite loop.

        Blocks need to open a scope.

        Examples:

            >>> with qp.infinite_loop():
            >>>    # operations that shall be executed in the infinite loop block

        Returns:
            InfiniteLoop: The infinite loop block.
        """
        return QProgram._InfiniteLoopContext(qprogram=self)

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

    def play(self, bus: str, waveform: Waveform | IQPair, wait_time: int | None = None):
        """Play a single waveform or an I/Q pair of waveforms on the bus.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (Waveform | IQPair): A single waveform or an I/Q pair of waveforms
        """
        operation = Play(bus=bus, waveform=waveform, wait_time=wait_time)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("duration", Domain.Time)
    def wait(self, bus: str, duration: int):
        """Adds a delay on the bus with a specified time.

        Args:
            bus (str): Unique identifier of the bus.
            time (int): Duration of the delay.
        """
        operation = Wait(bus=bus, duration=duration)
        self._active_block.append(operation)
        self._buses.add(bus)

    def acquire(self, bus: str, weights: IQPair):
        """Acquire results based on the given weights.

        Args:
            bus (str): Unique identifier of the bus.
            weights (IQPair): Weights used during acquisition.
        """
        operation = Acquire(bus=bus, weights=weights)
        self._active_block.append(operation)
        self._buses.add(bus)

    def measure(
        self,
        bus: str,
        waveform: IQPair,
        weights: IQPair | tuple[IQPair, IQPair] | tuple[IQPair, IQPair, IQPair, IQPair] | None = None,
        demodulation: bool = True,
        save_raw_adc: bool = False,
    ):
        """Play a pulse and acquire results.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (IQPair): Waveform played during measurement.
            weights (IQPair | tuple[IQPair, IQPair] | tuple[IQPair, IQPair, IQPair, IQPair] | None, optional): Weights used during acquisition. Defaults to None.
            demodulation (bool, optional): If demodulation is enabled. Defaults to True.
            save_raw_adc (bool, optional): If raw adc data should be saved. Defaults to True.
        """
        operation = Measure(
            bus=bus, waveform=waveform, weights=weights, demodulation=demodulation, save_raw_adc=save_raw_adc
        )
        self._active_block.append(operation)
        self._buses.add(bus)

    def sync(self, buses: list[str] | None = None):
        """Synchronize operations between buses, so the operations following will start at the same time.

        If no buses are given, then the synchronization will involve all buses present in the QProgram.

        Args:
            buses (list[str] | None, optional): List of unique identifiers of the buses. Defaults to None.
        """
        operation = Sync(buses=buses)
        self._active_block.append(operation)
        if buses:
            self._buses.update(buses)

    def reset_phase(self, bus: str):
        """Reset the absolute phase of the NCO associated with the bus.

        Args:
            bus (str): Unique identifier of the bus.
        """
        operation = ResetPhase(bus=bus)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("phase", Domain.Phase)
    def set_phase(self, bus: str, phase: float):
        """Set the absolute phase of the NCO associated with the bus.

        Args:
            bus (str): Unique identifier of the bus.
            phase (float): The new absolute phase of the NCO.
        """
        operation = SetPhase(bus=bus, phase=phase)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("frequency", Domain.Frequency)
    def set_frequency(self, bus: str, frequency: float):
        """Set the frequency of the NCO associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            frequency (float): The new frequency of the NCO.
        """
        operation = SetFrequency(bus=bus, frequency=frequency)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("gain", Domain.Voltage)
    def set_gain(self, bus: str, gain: float):
        """Set the gain of the AWG associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            gain (float): The new gain of the AWG.
        """
        operation = SetGain(bus=bus, gain=gain)
        self._active_block.append(operation)
        self._buses.add(bus)

    @requires_domain("offset_path0", Domain.Voltage)
    @requires_domain("offset_path1", Domain.Voltage)
    def set_offset(self, bus: str, offset_path0: float, offset_path1: float):
        """Set the gain of the AWG associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            offset_path0 (float): The new offset of the AWG for path0.
            offset_path1 (float): The new offset of the AWG for path1.
        """
        operation = SetOffset(bus=bus, offset_path0=offset_path0, offset_path1=offset_path1)
        self._active_block.append(operation)
        self._buses.add(bus)

    def variable(self, domain: Domain, type: type[int | float] | None = None):  # pylint: disable=redefined-builtin
        """Declare a variable.

        Args:
            type (int | float): The type of the variable.

        Raises:
            NotImplementedError: If an unsupported type is provided.

        Returns:
            IntVariable | FloatVariable: The variable.
        """

        def _int_variable(domain: Domain = Domain.Scalar) -> IntVariable:
            variable = IntVariable(domain)
            self._variables.append(variable)
            return variable

        def _float_variable(domain: Domain = Domain.Scalar) -> FloatVariable:
            variable = FloatVariable(domain)
            self._variables.append(variable)
            return variable

        if domain is Domain.Scalar and type is None:
            raise ValueError("You must specify a type in a scalar variable.")
        if domain is not Domain.Scalar and type is not None:
            raise ValueError("When declaring a variable of a specific domain, its type is inferred by its domain.")

        if domain is Domain.Scalar:
            if type == int:
                return _int_variable(domain)
            if type == float:
                return _float_variable(domain)

        if domain == Domain.Time:
            return _int_variable(domain)
        if domain in [Domain.Frequency, Domain.Phase, Domain.Voltage]:
            return _float_variable(domain)
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

    class _InfiniteLoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram"):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: InfiniteLoop = InfiniteLoop()

    class _ParallelContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram", loops: list[Loop | ForLoop]):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: Parallel = Parallel(loops=loops)

        def __enter__(self) -> Parallel:
            for loop in self.block.loops:
                loop.variable._source = ValueSource.Dependent
                loop.variable._value = None
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            for loop in self.block.loops:
                loop.variable._source = ValueSource.Free
            super().__exit__(exc_type, exc_value, exc_tb)

    class _LoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(  # pylint: disable=super-init-not-called
            self, qprogram: "QProgram", variable: Variable, values: np.ndarray
        ):
            self.qprogram = qprogram
            self.block: Loop = Loop(variable=variable, values=values)

        def __enter__(self) -> Loop:
            self.block.variable._source = ValueSource.Dependent
            self.block.variable._value = None
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.block.variable._source = ValueSource.Free
            super().__exit__(exc_type, exc_value, exc_tb)

    class _ForLoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(  # pylint: disable=super-init-not-called
            self, qprogram: "QProgram", variable: Variable, start: int | float, stop: int | float, step: int | float
        ):
            self.qprogram = qprogram
            self.block: ForLoop = ForLoop(variable=variable, start=start, stop=stop, step=step)

        def __enter__(self) -> ForLoop:
            self.block.variable._source = ValueSource.Dependent
            self.block.variable._value = None
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.block.variable._source = ValueSource.Free
            super().__exit__(exc_type, exc_value, exc_tb)

    class _AverageContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(self, qprogram: "QProgram", shots: int):  # pylint: disable=super-init-not-called
            self.qprogram = qprogram
            self.block: Average = Average(shots=shots)
