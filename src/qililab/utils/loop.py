"""Loop class."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Loop:
    """Loop class."""

    category: str
    id_: int
    parameter: str
    start: float
    stop: float
    num: int
    loop: Loop | None = None
    previous: Loop | None = None

    def __post_init__(self):
        """Overwrite 'previous' attribute of next loop with self."""
        if self.loop is not None:
            self.loop.previous = self

    @property
    def range(self) -> np.ndarray:
        """ExperimentLoop 'range' property.

        Returns:
            ndarray: Range of values of loop.
        """
        return np.linspace(start=self.start, stop=self.stop, num=self.num)
