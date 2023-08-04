from dataclasses import dataclass

from qililab.qprogram.blocks.block import Block


@dataclass
class AcquireLoop(Block):  # pylint: disable=missing-class-docstring
    iterations: int
    bins: int = 1
