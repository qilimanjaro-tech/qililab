"""Results class."""
from dataclasses import dataclass, field
from types import NoneType
from typing import List

import numpy as np

from qililab.constants import RUNCARD
from qililab.result.qblox_result import QbloxResult
from qililab.result.result import Result
from qililab.utils.factory import Factory
from qililab.utils.loop import Loop


@dataclass
class Results:
    """Results class."""

    software_average: int
    num_sequences: int
    loop: Loop | None = None
    shape: List[int] = field(default_factory=list)
    results: List[Result] = field(default_factory=list)

    def __post_init__(self):
        """Add num_sequences to shape."""
        if not self.shape:
            self.shape = self.loop.shape if self.loop is not None else []
            if self.num_sequences > 1:
                self.shape.append(self.num_sequences)
            if self.software_average > 1:
                self.shape.append(self.software_average)
        if self.results and isinstance(self.results[0], dict):
            # Pop the result name (qblox, simulator) from the dictionary and instantiate its corresponding Result class.
            self.results = [Factory.get(result.pop(RUNCARD.NAME))(**result) for result in self.results]
        if isinstance(self.loop, dict):
            self.loop = Loop(**self.loop)

    def add(self, result: List[Result]):
        """Append an ExecutionResults object.

        Args:
            execution_results (ExecutionResults): ExecutionResults object.
        """
        self.results += result

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

    def acquisitions(self, mean: bool = False) -> np.ndarray:
        """QbloxResult acquisitions of all the nested Results classes.

        Returns:
            np.ndarray: Acquisition values.
        """
        if not isinstance(self.results[0], QbloxResult):
            raise ValueError(f"{type(self.results[0]).__name__} class doesn't have an acquisitions method.")
        result_shape = self.results[0].shape
        self._fill_missing_values()
        results = []
        for result in self.results:
            if not isinstance(result, (QbloxResult, NoneType)):
                raise ValueError(f"{type(result).__name__} class doesn't have an acquisitions method.")
            results.append(
                result.acquisitions() if result is not None else np.full(shape=result_shape, fill_value=np.nan)
            )
        array = np.reshape(a=np.array(results), newshape=self.shape + result_shape)
        flipped_array = np.moveaxis(a=array, source=array.ndim - 1, destination=0)
        if mean and self.software_average > 1:
            flipped_array = np.mean(a=flipped_array, axis=-1)
        return flipped_array

    def _fill_missing_values(self):
        """Fill with None the missing values."""
        self.results += [None] * int(np.prod(self.shape) - len(self.results))

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
        return np.array(ranges, dtype=object).squeeze()
