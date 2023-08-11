from dataclasses import dataclass

from qililab.qprogram.blocks.block import Block


@dataclass(frozen=True)
class Average(Block):  # pylint: disable=missing-class-docstring
    shots: int
