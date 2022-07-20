"""Loop class."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from qililab.constants import LOOP, RUNCARD
from qililab.typings.enums import Instrument, Parameter


@dataclass
class Loop:
    """Loop class."""

    parameter: Parameter
    start: float
    stop: float
    alias: str | None = None
    instrument: Instrument | None = None
    id_: int | None = None
    num: int | None = None
    step: float | None = None
    loop: Loop | None = None
    previous: Loop | None = field(compare=False, default=None)

    def __post_init__(self):
        """Check that either step or num is used. Overwrite 'previous' attribute of next loop with self."""
        if self.step is not None and self.num is not None:
            raise ValueError("'step' and 'num' arguments cannot be used together.")
        if self.loop is not None:
            if isinstance(self.loop, dict):
                self.loop = Loop(**self.loop)
            self.loop.previous = self
        if isinstance(self.instrument, str):
            self.instrument = Instrument(self.instrument)
        if isinstance(self.parameter, str):
            self.parameter = Parameter(self.parameter)

    @property
    def range(self) -> np.ndarray:
        """Loop 'range' property.

        Returns:
            ndarray: Range of values of first loop.
        """
        if self.num is not None:
            return np.linspace(start=self.start, stop=self.stop, num=self.num)
        if self.step is not None:
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
        if len(self.loops) != 2:
            return None
        return self.loops[-2].range

    def to_dict(self) -> dict:
        """Convert class to a dictionary.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            RUNCARD.ALIAS: self.alias,
            RUNCARD.INSTRUMENT: self.instrument.value if self.instrument is not None else None,
            RUNCARD.ID: self.id_,
            LOOP.PARAMETER: self.parameter.value,
            LOOP.START: self.start,
            LOOP.STOP: self.stop,
            LOOP.NUM: self.num,
            LOOP.STEP: self.step,
            LOOP.LOOP: self.loop.to_dict() if self.loop is not None else None,
        }
