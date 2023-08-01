from dataclasses import dataclass

from qililab.qprogram.blocks.block import Block


@dataclass(frozen=True)
class AcquireLoop(Block):
    iterations: int
