"""Results class."""
from dataclasses import dataclass, field
from typing import List

import numpy as np

from qililab.result.qblox_result import QbloxResult
from qililab.result.result import Result


@dataclass
class Results:
    """Results class."""

    software_average: int
    shape: List[int] = field(default_factory=list)
    num_sequences: int = 1
    results: List[Result] = field(default_factory=list)

    def __post_init__(self):
        """Add num_sequences to shape."""
        if self.num_sequences > 1:
            self.shape.append(self.num_sequences)
        if self.software_average > 1:
            self.shape.append(self.software_average)

    def add(self, result: Result | List[Result]):
        """Append an ExecutionResults object.

        Args:
            execution_results (ExecutionResults): ExecutionResults object.
        """
        if isinstance(result, list):
            self.results += result
        else:
            self.results.append(result)

    def probabilities(self) -> np.ndarray:
        """Probabilities of being in the ground and excited state of all the nested Results classes.

        Returns:
            np.ndarray: List of probabilities of each executed loop and sequence.
        """
        probs = [result.probabilities() for result in self.results]
        array = np.reshape(a=probs, newshape=self.shape + [2])
        return np.moveaxis(a=array, source=array.ndim - 1, destination=0)

    def acquisitions(self, mean: bool = True) -> np.ndarray:
        """QbloxResult acquisitions of all the nested Results classes.

        Returns:
            np.ndarray: Acquisition values.
        """
        results = []
        for result in self.results:
            if not isinstance(result, QbloxResult):
                raise ValueError(f"{type(result).__name__} class doesn't have an acquisitions method.")
            results.append(result.acquisitions())
        array = np.reshape(a=results, newshape=self.shape + [4])
        flipped_array = np.moveaxis(a=array, source=array.ndim - 1, destination=0)
        if mean:
            flipped_array = np.mean(a=flipped_array, axis=-1)
        return flipped_array
