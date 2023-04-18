"""Loop class."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from qililab.constants import LOOP
from qililab.typings.enums import Parameter


@dataclass
class Loop:
    """Loop class."""

    alias: str
    parameter: Parameter
    range: np.ndarray
    loop: Loop | None = None
    previous: Loop | None = field(compare=False, default=None)
    channel_id: int | None = None

    def __post_init__(self):
        """Check that either step or num is used. Overwrite 'previous' attribute of next loop with self."""
        if self.loop is not None:
            if isinstance(self.loop, dict):
                self.loop = Loop(**self.loop)
            self.loop.previous = self
        if isinstance(self.parameter, str):
            self.parameter = Parameter(self.parameter)

    @property
    def ranges(self) -> np.ndarray:
        """Loop 'ranges' property.

        Returns:
            list: Range of values of all loops.
        """
        ranges = [loop.range for loop in self.loops]
        return np.array(ranges, dtype=object)

    @property
    def shape(self) -> List[int]:
        """Return number of points of all loops.

        Returns:
            list: List containing the number of points of all loops.
        """
        shape = []
        loop: Loop | None = self
        while loop is not None:
            shape.append(int(loop.num))
            loop = loop.loop
        return shape

    @property
    def num_loops(self) -> int:
        """Loop 'num_loops' property.

        Returns:
            int: Number of nested loops.
        """
        return len(self.loops)

    @property
    def loops(self) -> List[Loop]:
        """Loop 'loops' property.

        Returns:
            List[Loop]: List of loop objects.
        """
        loops = []
        loop: Loop | None = self
        while loop is not None:
            loops.append(loop)
            loop = loop.loop
        return loops

    @property
    def outer_loop_range(self) -> np.ndarray:
        """return the range of the outer loop"""
        if len(self.loops) <= 0:
            raise ValueError("Loop MUST contain at least one loop")
        return self.loops[-1].range

    @property
    def inner_loop_range(self) -> np.ndarray | None:
        """Return the range of the inner loop or None
        when there are not exactly two loops.
        """
        return None if len(self.loops) != 2 else self.loops[-2].range

    def to_dict(self) -> dict:
        """Convert class to a dictionary.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            LOOP.ALIAS: self.alias,
            LOOP.PARAMETER: self.parameter.value,
            LOOP.RANGE: self.range,
            LOOP.LOOP: self.loop.to_dict() if self.loop is not None else None,
            LOOP.CHANNEL_ID: self.channel_id,
        }

    @property
    def start(self):
        """returns 'start' options property."""
        return self.range[0]

    @property
    def stop(self):
        """returns 'stop' options property."""
        return self.range[-1]

    @property
    def num(self):
        """returns 'num' options property."""
        return len(self.range)
