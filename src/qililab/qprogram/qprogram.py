from collections import deque
from typing import Self, TypeVar

from qililab.qprogram.blocks.block import Block
from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.operations.wait import Wait
from qililab.qprogram.variable import FloatVariable, IntVariable
from qililab.waveforms.waveform import Waveform

T = TypeVar("T")


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
        return QProgram._BlockContext(qprogram=self)

    def acquire_loop(self, iterations: int = 1000, bins: int = 1):
        pass

    def loop(self):
        pass

    def play(self, bus: str, waveform: Waveform | tuple[Waveform, Waveform]):
        pass

    def acquire(self, bus: str, weights: Waveform | None = None):
        pass

    def sync(self, buses: list[str]):
        pass

    def variable(self, type: int | float):
        """Declare a variable.

        Args:
            type (int | float): The type of the variable.

        Raises:
            NotImplementedError: If an unsupported type is provided.

        Returns:
            IntVariable | FloatVariable: The variable.
        """
        if type == int:
            return self._int_variable()
        elif type == float:
            return self._float_variable()
        else:
            raise NotImplementedError

    def _int_variable(self, value: int = 0) -> IntVariable:
        """Declare an integer variable

        Args:
            value (int, optional): Initial value of the variable. Defaults to 0.

        Returns:
            IntVariable: An instance of an integer variable
        """
        variable = IntVariable(value)
        self.variables.append(variable)
        return variable

    def _float_variable(self, value: float = 0.0) -> FloatVariable:
        """Declare a float variable

        Args:
            value (float, optional): Initial value of the variable. Defaults to 0.0.

        Returns:
            FloatVariable: An instance of a float variable
        """
        variable = FloatVariable(value)
        self.variables.append(variable)
        return variable

    def wait(self, bus: str, time: int):
        """Adds a delay on the bus with a specified time.

        Args:
            bus (str): Unique identifier of the bus where the delay should be applied.
            time (int): Duration of the delay.
        """
        operation = Wait(bus=bus, time=time)
        self._active_block.append(operation)

    class _BlockContext:
        def __init__(self, qprogram: Self):
            self.qprogram = qprogram
            self.block = Block()

        def __enter__(self):
            self.qprogram._append_to_block_stack(block=self.block)
            return self.block

        def __exit__(self, exc_type, exc_value, exc_tb):
            block = self.qprogram._pop_from_block_stack()
            self.qprogram._append_to_active_block(block)
