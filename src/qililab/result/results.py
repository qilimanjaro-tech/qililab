"""Results class."""
from dataclasses import dataclass, field
from types import NoneType
from typing import List

import numpy as np

from qililab.constants import YAML
from qililab.result.qblox_result import QbloxResult
from qililab.result.result import Result
from qililab.utils import Factory, Loop


@dataclass
class Results:
    """Results class."""

    software_average: int
    num_sequences: int
    shape: List[int] = field(default_factory=list)
    results: List[Result | None] = field(default_factory=list)
    loop: Loop | None = None

    def __post_init__(self):
        """Add num_sequences to shape."""
        if not self.shape:
            self.shape = self.loop.shape if self.loop is not None else []
            if self.num_sequences > 1:
                self.shape.append(self.num_sequences)
            if self.software_average > 1:
                self.shape.append(self.software_average)
        if self.results and isinstance(self.results[0], dict):
            self.results = [Factory.get(result.pop(YAML.NAME))(**result) for result in self.results]

    def add(self, result: Result | List[Result]):
        """Append an ExecutionResults object.

        Args:
            execution_results (ExecutionResults): ExecutionResults object.
        """
        if isinstance(result, list):
            self.results += result
        else:
            self.results.append(result)

    def probabilities(self, mean: bool = True) -> np.ndarray:
        """Probabilities of being in the ground and excited state of all the nested Results classes.

        Returns:
            np.ndarray: List of probabilities of each executed loop and sequence.
        """
        self._fill_missing_values()
        probs = [result.probabilities() if result is not None else (np.nan, np.nan) for result in self.results]
        array = np.reshape(a=probs, newshape=self.shape + [2])
        flipped_array = np.moveaxis(a=array, source=array.ndim - 1, destination=0)
        if mean and self.software_average > 1:
            flipped_array = np.mean(a=flipped_array, axis=-1)
        return flipped_array

    def acquisitions(self, mean: bool = True) -> np.ndarray:
        """QbloxResult acquisitions of all the nested Results classes.

        Returns:
            np.ndarray: Acquisition values.
        """
        self._fill_missing_values()
        results = []
        for result in self.results:
            if not isinstance(result, (QbloxResult, NoneType)):
                raise ValueError(f"{type(result).__name__} class doesn't have an acquisitions method.")
            results.append(result.acquisitions() if result is not None else (np.nan, np.nan, np.nan, np.nan))
        array = np.reshape(a=results, newshape=self.shape + [4])
        flipped_array = np.moveaxis(a=array, source=array.ndim - 1, destination=0)
        if mean and self.software_average > 1:
            flipped_array = np.mean(a=flipped_array, axis=-1)
        return flipped_array

    def _fill_missing_values(self):
        """Fill with None the missing values."""
        self.results += [None] * (np.prod(self.shape) - len(self.results))

    @property
    def ranges(self) -> np.ndarray:
        """Results 'ranges' property.

        Returns:
            list: Values of the loops.
        """
        if self.loop is None:
            raise ValueError("Loop must not be None.")
        ranges = []
        loop: Loop | None = self.loop
        while loop is not None:
            ranges.append(loop.range)
            loop = loop.loop
        return np.array(ranges)
