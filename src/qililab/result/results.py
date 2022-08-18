"""Results class."""
from copy import deepcopy
from dataclasses import dataclass, field
from types import NoneType
from typing import List, Tuple

import numpy as np

from qililab.constants import EXPERIMENT, RUNCARD
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.result.result import Result
from qililab.utils.factory import Factory
from qililab.utils.loop import Loop
from qililab.utils.util_loops import (
    compute_ranges_from_loops,
    compute_shapes_from_loops,
)


@dataclass
class Results:
    """Results class."""

    software_average: int
    num_sequences: int
    loops: List[Loop] | None = None
    shape: List[int] = field(default_factory=list)
    results: List[Result] = field(default_factory=list)

    def __post_init__(self):
        """Add num_sequences to shape."""
        if not self.shape:
            self.shape = compute_shapes_from_loops(loops=self.loops)
        if self.num_sequences > 1:
            self.shape.append(self.num_sequences)
        if self.software_average > 1:
            self.shape.append(self.software_average)
        if self.results and isinstance(self.results[0], dict):
            tmp_results = deepcopy(self.results)
            # Pop the result name (qblox, simulator) from the dictionary and instantiate its corresponding Result class.
            self.results = [Factory.get(result.pop(RUNCARD.NAME))(**result) for result in tmp_results]
        if self.loops is not None and isinstance(self.loops[0], dict):
            self.loops = [Loop(**loop) for loop in self.loops]

    def add(self, result: List[Result]):
        """Append an ExecutionResults object.

        Args:
            result (List[Result]): List of Result objects.
        """
        self.results += result

    def probabilities(self, mean: bool = True) -> np.ndarray:
        """Probabilities of being in the ground and excited state of all the nested Results classes.

        Returns:
            np.ndarray: List of probabilities of each executed loop and sequence.
        """
        self._fill_missing_values()
        num_qubits = len(self.results[0].probabilities())
        probs: List[List[Tuple[float, float]]] = [[] for _ in range(num_qubits)]
        for result in self.results:
            result_probs = result.probabilities()
            for idx, result_prob in enumerate(result_probs):
                probs[idx].append(result_prob)
        array = np.reshape(a=probs, newshape=[num_qubits] + self.shape + [2])
        flipped_array = np.moveaxis(a=array, source=array.ndim - 1, destination=0)
        if mean and self.software_average > 1:
            flipped_array = np.mean(a=flipped_array, axis=-1)
        return flipped_array.squeeze()

    def acquisitions(self, mean: bool = False) -> np.ndarray:
        """QbloxResult acquisitions of all the nested Results classes.

        Returns:
            np.ndarray: Acquisition values.
        """
        if not isinstance(self.results[0], QbloxResult):
            raise ValueError(f"{type(self.results[0]).__name__} class doesn't have an acquisitions method.")
        result_shape = self.results[0].shape
        self._fill_missing_values()
        results: List[List[np.ndarray]] = [[] for _ in range(result_shape[0])]
        for result in self.results:
            if not isinstance(result, (QbloxResult, NoneType)):
                raise ValueError(f"{type(result).__name__} class doesn't have an acquisitions method.")
            result_values = (
                result.acquisitions() if result is not None else np.full(shape=result_shape, fill_value=np.nan)
            )
            for result_idx, result_value in enumerate(result_values):
                results[result_idx].append(result_value)
        array = np.reshape(a=np.array(results), newshape=[result_shape[0]] + self.shape + result_shape[1:])
        flipped_array = np.moveaxis(a=array, source=array.ndim - 1, destination=1)
        if mean and self.software_average > 1:
            flipped_array = np.mean(a=flipped_array, axis=-1)
        return flipped_array.squeeze()

    def _fill_missing_values(self):
        """Fill with None the missing values."""
        self.results += [None] * int(np.prod(self.shape) - len(self.results))

    @property
    def ranges(self) -> np.ndarray:
        """Results 'ranges' property.

        Returns:
            list: Values of the loops.
        """
        if self.loops is None:
            raise ValueError("Results doesn't contain a loop.")

        ranges = compute_ranges_from_loops(loops=self.loops)
        return np.array(ranges, dtype=object).squeeze()

    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """
        return {
            EXPERIMENT.SOFTWARE_AVERAGE: self.software_average,
            EXPERIMENT.NUM_SEQUENCES: self.num_sequences,
            EXPERIMENT.SHAPE: [] if self.loops is None else compute_shapes_from_loops(loops=self.loops),
            EXPERIMENT.LOOPS: [loop.to_dict() for loop in self.loops] if self.loops is not None else None,
            EXPERIMENT.RESULTS: [result.to_dict() for result in self.results],
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Transforms a dictionary into a Results instance. Inverse of to_dict().
        Args:
            dictionary: dict representation of a Results instance
        Returns:
            Results: deserialized Results instance
        """
        return Results(**dictionary)
