"""Loop class."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class Loop:
    """Loop class."""

    category: str
    id_: int
    parameter: str
    start: float
    stop: float
    num: int | None = None
    step: float | None = None
    loop: Loop | None = None
    previous: Loop | None = None

    def __post_init__(self):
        """Check that either step or num is used. Overwrite 'previous' attribute of next loop with self."""
        if self.step is not None and self.num is not None:
            raise ValueError("'step' and 'num' arguments cannot be used together.")
        if self.loop is not None:
            self.loop.previous = self

    @property
    def range(self) -> np.ndarray:
        """ExperimentLoop 'range' property.

        Returns:
            ndarray: Range of values of loop.
        """
        if self.num is not None:
            return np.linspace(start=self.start, stop=self.stop, num=self.num)
        elif self.step is not None:
            return np.arange(start=self.start, stop=self.stop, step=self.step)
        else:
            raise ValueError("Please specify either 'step' or 'num' arguments.")

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
        num_loops = 0
        loop: Loop | None = self
        while loop is not None:
            num_loops += 1
            loop = loop.loop
        return num_loops
