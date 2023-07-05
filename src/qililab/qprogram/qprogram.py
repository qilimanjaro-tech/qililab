from collections import deque
from typing import Self

from numpy import ndarray

from qililab.qprogram.blocks.block import Block
from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.operations.wait import Wait
from qililab.waveforms.waveform import Waveform


class QProgram:
    def __init__(self):
        self.program: Block = Block()
        self._block_stack: deque[Block] = deque()
        self._block_stack.append(self.program)

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

    def wait(self, bus: str, time: int):
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
