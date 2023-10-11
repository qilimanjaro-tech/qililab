import math
from collections import deque
from typing import Any, Callable

import numpy as np
import qm.qua as qua

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


# pylint: disable=protected-access
class CompilationInfo:  # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Class representing the information stored by QBloxCompiler for a bus."""

    def __init__(self):
        # The generated Sequence
        self.qua_program = qua.program()


class QuantumMachinesCompiler:
    """_summary_"""

    def __init__(self):
        # Handlers to map each operation to a corresponding handler function
        self._handlers: dict[type, Callable] = {}

        self._qprogram: QProgram
        self.qprogram_block_stack: deque[Block] = deque()
        self.qprogram_to_qua_variables: dict[Variable, qua.QuaVariableType] = {}

    def compile(self, qprogram: QProgram) -> qua.Program:
        """Compile QProgram to QUA's Program.

        Args:
            qprogram (QProgram): The QProgram to be compiled

        Returns:
            qua.Program: The compiled program.
        """

        def traverse(block: Block):
            self.qprogram_block_stack.append(block)
            for element in block.elements:
                handler = self._handlers.get(type(element))
                if not handler:
                    raise NotImplementedError(f"{element.__class__} is currently not supported in QBlox.")
                if isinstance(element, Block):
                    traverse(element)
            self.qprogram_block_stack.pop()

        self._qprogram = qprogram
        with qua.program() as qua_program:
            # Recursive traversal to convert QProgram blocks to Sequence
            traverse(self._qprogram._program)

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        return qua_program
