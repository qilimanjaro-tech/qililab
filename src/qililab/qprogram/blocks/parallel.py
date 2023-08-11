from dataclasses import dataclass

from qililab.qprogram.blocks.block import Block
from qililab.qprogram.blocks.for_loop import ForLoop


@dataclass(frozen=True)
class Parallel(Block):  # pylint: disable=missing-class-docstring
    loops: list[ForLoop]
