from dataclasses import dataclass

from qililab.qprogram.blocks.block import Block


@dataclass
class AcquireLoop(Block):
    iterations: int
    bins: int = 1
