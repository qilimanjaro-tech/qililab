from dataclasses import dataclass

from qililab.qprogram.blocks.block import Block
from qililab.qprogram.variable import Variable


@dataclass(frozen=True)
class ForLoop(Block):
    variable: Variable
    start: int | float
    stop: int | float
    step: int | float
