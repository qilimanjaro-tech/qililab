from collections import deque
from typing import Self

import numpy as np

from qililab.qprogram.blocks.acquire_loop import AcquireLoop
from qililab.qprogram.blocks.block import Block
from qililab.qprogram.blocks.loop import Loop
from qililab.qprogram.operations.acquire import Acquire
from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.operations.play import Play
from qililab.qprogram.operations.reset_phase import ResetPhase
from qililab.qprogram.operations.set_gain import SetGain
from qililab.qprogram.operations.set_nco_frequency import SetNCOFrequency
from qililab.qprogram.operations.sync import Sync
from qililab.qprogram.operations.wait import Wait
from qililab.qprogram.variable import FloatVariable, IntVariable, Variable
from qililab.waveforms import IQPair, Waveform


class QProgram:
    def __init__(self):
        self.variables = []
        self.program: Block = Block()

        self._block_stack: deque[Block] = deque([self.program])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._block_stack.pop()

    def _append_to_block_stack(self, block: Block):
        self._block_stack.append(block)

    def _pop_from_block_stack(self):
        return self._block_stack.pop()

    @property
    def _active_block(self) -> Block:
        return self._block_stack[-1]

    def _append_to_active_block(self, element: Block | Operation):
        self._active_block.append(element=element)

    def block(self):
        """Define a generic block for scoping operations.

        Blocks need to open a scope in the following way::

            with qp.block(...):
                # here come the operations that shall be executed in the block

        Returns:
            Block: The block.
        """
        return QProgram._BlockContext(qprogram=self)

    def acquire_loop(self, iterations: int, bins: int = 1):
        """Define an acquire loop block with averaging in real time.

        Blocks need to open a scope in the following way::

            with qp.acquire_loop(...):
                # here come the operations that shall be executed in the acquire_loop block

        Args:
            iterations (int): The number of acquire iterations.
            bins (int, optional): The number of bins used for acquisition. Defaults to 1.

        Returns:
            AcquireLoop: The acquire_loop block.
        """
        return QProgram._AcquireLoopContext(qprogram=self, iterations=iterations, bins=bins)

    def loop(self, variable: Variable, values: np.ndarray):
        """Define a loop block to iterate values over a variable.

        Blocks need to open a scope in the following way::

            with qp.loop(...):
                # here come the operations that shall be executed in the loop block

        Args:
            variable (Variable): The variable to be affected from the loop.
            values (np.ndarray): The values to iterate over.

        Returns:
            Loop: The loop block.
        """

        return QProgram._LoopContext(qprogram=self, variable=variable, values=values)

    def play(self, bus: str, waveform: Waveform | IQPair):
        """Play a single waveform or an I/Q pair of waveforms on the bus

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
        """Acquire results

        Args:
            bus (str): Unique identifier of the bus.
            weights (IQPair | None, optional): Weights used during acquisition. Defaults to None.
        """
        operation = Acquire(bus=bus, weights=weights)
        self._active_block.append(operation)

    def sync(self, buses: list[str]):
        """Synchronize between buses

        Args:
            buses (list[str]): List of unique idetifiers of the buses.
        """
        operation = Sync(buses=buses)
        self._active_block.append(operation)

    def reset_nco_phase(self, bus: str):
        """Reset the phase of the NCO associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
        """
        operation = ResetPhase(bus=bus)
        self._active_block.append(operation)

    def set_nco_frequency(self, bus: str, frequency: int):
        """Set the frequency of the NCO associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            frequency (int): The new frequency of the NCO.
        """
        operation = SetNCOFrequency(bus=bus, frequency=frequency)
        self._active_block.append(operation)

    def set_awg_gain(self, bus: str, gain: float):
        """Set the gain of the AWG associated with bus.

        Args:
            bus (str): Unique identifier of the bus.
            gain (float): The new gain of the AWG.
        """
        operation = SetGain(bus=bus, gain=gain)
        self._active_block.append(operation)

    def variable(self, type: int | float):
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
            self.variables.append(variable)
            return variable

        def _float_variable(value: float = 0.0) -> FloatVariable:
            variable = FloatVariable(value)
            self.variables.append(variable)
            return variable

        if type == int:
            return _int_variable()
        elif type == float:
            return _float_variable()
        else:
            raise NotImplementedError

    class _BlockContext:
        def __init__(self, qprogram: "QProgram"):
            self.qprogram = qprogram
            self.block = Block()

        def __enter__(self):
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block

        def __exit__(self, exc_type, exc_value, exc_tb):
            block = self.qprogram._pop_from_block_stack()
            self.qprogram._append_to_active_block(block)

    class _LoopContext(_BlockContext):
        def __init__(self, qprogram: "QProgram", variable: Variable, values: np.ndarray):
            self.qprogram = qprogram
            self.block = Loop(variable=variable, values=values)

    class _AcquireLoopContext(_BlockContext):
        def __init__(self, qprogram: "QProgram", iterations: int, bins: int):
            self.qprogram = qprogram
            self.block = AcquireLoop(iterations=iterations, bins=bins)
