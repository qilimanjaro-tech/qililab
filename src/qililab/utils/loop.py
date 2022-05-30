"""Loop class."""
from dataclasses import dataclass

import numpy as np

from qililab.typings import Category


@dataclass
class Loop:
    """Loop class."""

    category: str | Category
    id_: int
    parameter: str
    start: float
    stop: float
    num: int

    def __post_init__(self):
        """Cast category to its corresponding class."""
        self.category = Category(self.category)

    @property
    def range(self) -> np.ndarray:
        """ExperimentLoop 'range' property.

        Returns:
            ndarray: Range of values of loop.
        """
        return np.linspace(start=self.start, stop=self.stop, num=self.num)
