"""Loop class."""
from dataclasses import dataclass

import numpy as np

from qililab.typings import Category


@dataclass
class Loop:
    """Loop class."""

    category: str
    id_: int
    parameter: str
    start: float
    stop: float
    num: int

    @property
    def range(self) -> np.ndarray:
        """ExperimentLoop 'range' property.

        Returns:
            ndarray: Range of values of loop.
        """
        return np.linspace(start=self.start, stop=self.stop, num=self.num)
