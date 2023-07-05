from collections import deque

from qililab.qprogram.blocks.block import Block
from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.operations.wait import Wait


class QProgram:
    def __init__(self):
        self.program: Block = Block()
        self._block_stack: deque[Block] = deque()
        self._block_stack.append(self.program)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._block_stack.pop()

    def _append_block(self, block: Block):
        self._block_stack.append(block)

    def _pop_block(self):
        return self._block_stack.pop()

    def _active_block(self) -> Block:
        return self._block_stack[-1]

    def _append_to_active_block(self, element: Block | Operation):
        self._block_stack[-1].append(element=element)

    def block(self):
        return QProgram._BlockContext(qprogram=self)

    def wait(self, bus: str, time: int):
        active_block = self._active_block()
        operation = Wait(bus=bus, time=time)
        active_block.append(operation)

    class _BlockContext:
        def __init__(self, qprogram: "QProgram"):
            self.qprogram = qprogram
            self.block = Block()

        def __enter__(self):
            self.qprogram._append_block(block=self.block)
            return self.block

        def __exit__(self, exc_type, exc_value, exc_tb):
            block = self.qprogram._pop_block()
            self.qprogram._append_to_active_block(block)
