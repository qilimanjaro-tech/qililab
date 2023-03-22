"""Loop class."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import List

import numpy as np

from qililab.constants import LOOP
from qililab.typings.enums import Parameter
from qililab.typings.loop import LoopOptions


@dataclass
class Loop:
    """Loop class."""

    alias: str
    parameter: Parameter
    options: LoopOptions
    loop: Loop | None = None
    previous: Loop | None = field(compare=False, default=None)
    hardware: bool = False

    def __post_init__(self):
        """Check that either step or num is used. Overwrite 'previous' attribute of next loop with self."""
        if isinstance(self.options, dict):
            self.options = LoopOptions(**self.options)  # pylint: disable=not-a-mapping
        if self.loop is not None:
            if isinstance(self.loop, dict):
                self.loop = Loop(**self.loop)
            if self.hardware is True:
                if self.loop.hardware is False:
                    raise ValueError("Cannot add a software loop inside a hardware loop.")
                if self.alias != self.loop.alias:
                    raise ValueError("Nested hardware loops of parameters of different buses is not supported.")

            self.loop.previous = self
        if isinstance(self.parameter, str):
            self.parameter = Parameter(self.parameter)

    @property
    def range(self) -> np.ndarray:
        """Loop 'range' property.

        Returns:
            ndarray: Range of values of first loop.
        """
        if self.values is not None:
            return self.values
        if self.logarithmic and self.num is not None:
            return np.geomspace(start=self.start, stop=self.stop, num=self.num)  # type: ignore
        if self.num is not None:
            return np.linspace(start=self.start, stop=self.stop, num=self.num)  # type: ignore
        if self.options.step is not None:
            return np.arange(start=self.start, stop=self.stop, step=self.step)

        raise ValueError("Please specify either 'step' or 'num' arguments.")

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
            if loop.num is not None:
                shape.append(int(loop.num))
            elif loop.step is not None:
                shape.append(int(np.ceil((loop.stop - loop.start) / loop.step)))
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
    def hw_loop(self) -> Loop | None:
        """Returns a Loop object containing only the hardware loops.

        Returns:
            Loop | None: Loop object containing only the hardware loops. If the initial Loop is software, ``None`` is
                returned.
        """
        if not self.hardware:
            # If Loop is already a hardware loop, return None
            return None
        loop: Loop | None = copy.deepcopy(self)
        while loop is not None and not loop.hardware:
            loop = loop.loop

        return loop

    @property
    def sw_loop(self) -> Loop | None:
        """Returns a Loop object containing only the software loops.

        Returns:
            Loop | None: Loop object containing only the software loops. If the initial Loop is hardware, ``None`` is
                returned.
        """
        if self.hardware:
            # If Loop is already a hardware loop, return None
            return None
        loop: Loop | None = copy.deepcopy(self)
        tmp_loop = loop
        while tmp_loop.loop is not None:
            if tmp_loop.loop.hardware:
                tmp_loop.loop = None
                break
            tmp_loop = tmp_loop.loop

        return loop

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
            LOOP.OPTIONS: asdict(self.options),
            LOOP.LOOP: self.loop.to_dict() if self.loop is not None else None,
        }

    @property
    def start(self):
        """returns 'start' options property."""
        if self.options.start is None:
            raise ValueError("'start' cannot be None")
        return self.options.start

    @property
    def stop(self):
        """returns 'stop' options property."""
        if self.options.stop is None:
            raise ValueError("'stop' cannot be None")
        return self.options.stop

    @property
    def num(self):
        """returns 'num' options property."""
        return self.options.num

    @property
    def step(self):
        """returns 'step' options property."""
        if self.options.step is not None:
            return self.options.step
        return (self.stop - self.start) / self.num

    @property
    def logarithmic(self):
        """returns 'logarithmic' options property."""
        return self.options.logarithmic

    @property
    def channel_id(self):
        """returns 'channel_id' options property."""
        return self.options.channel_id

    @property
    def values(self):
        """returns 'values' options property."""
        return self.options.values
