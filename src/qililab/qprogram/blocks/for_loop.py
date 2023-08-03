from dataclasses import dataclass

from qililab.qprogram.blocks.block import Block
from qililab.qprogram.variable import Variable


@dataclass(frozen=True)
class ForLoop(Block):  # pylint: disable=missing-class-docstring
    variable: Variable
    start: int | float
    stop: int | float
    step: int | float
