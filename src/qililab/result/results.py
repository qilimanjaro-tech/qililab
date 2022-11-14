"""Results class."""
from copy import deepcopy
from dataclasses import dataclass, field
from types import NoneType
from typing import List, Tuple

import numpy as np
import pandas as pd

from qililab.constants import EXPERIMENT, RUNCARD
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.result.result import Result
from qililab.utils.factory import Factory
from qililab.utils.loop import Loop
from qililab.utils.util_loops import (
    compute_ranges_from_loops,
    compute_shapes_from_loops,
)
from qililab.utils import coordinate_decompose


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

    def _generate_new_probabilities_column_names(self):
        """ Checks shape, num_sequence and software_average and returns with that the list of columns that should
         be added to the dataframe. """
        new_columns = ['qubit_index',
                       *[f'loop_index_{i}' for i in range(len(compute_shapes_from_loops(loops=self.loops)))]
                       ]
        if self.num_sequences > 1:
            new_columns.append('sequence_index')
        if self.software_average > 1:
            new_columns.append('software_avg_index')
        return new_columns

    def _concatenate_probabilities_dataframes(self):
        """ Concatenates the probabilities dataframes from all the results"""
        result_probabilities_list = [result.probabilities() if result is not None
                                     else pd.DataFrame([]).reindex_like(self.results[0].probabilities())
                                     for result in self.results]
        return pd.concat(result_probabilities_list, keys=range(len(result_probabilities_list)),
                         names=['result_index']).reset_index()

    def _add_meaningful_probabilities_indices(self, result_probabilities_dataframe: pd.DataFrame) -> pd.DataFrame:
        """ Add to the dataframe columns that are relevant indices, computable from the `result_index`, as:
        `loop_index_n` (in case more than one loop is defined), `sequence_index`"""
        old_columns = result_probabilities_dataframe.columns
        new_columns = self._generate_new_probabilities_column_names()

        num_qbits = len(self.results[0].probabilities())

        result_probabilities_dataframe[new_columns] = result_probabilities_dataframe.apply(
            lambda row: coordinate_decompose(
                new_dimension_shape=[num_qbits, *self.shape],
                original_size=len(self.results),
                original_idx=row['result_index']),
            axis=1,
            result_type='expand')
        return result_probabilities_dataframe.reindex(columns=[*new_columns, *old_columns], copy=True)

    def _process_dataframe_if_needed(self, result_dataframe: pd.DataFrame, mean: bool = False):
        """ Process the dataframe by applying software average if required """

        if mean and self.software_average > 1:
            return result_dataframe.groupby('software_avg_index').mean()
        return result_dataframe

    def probabilities(self, mean: bool = True) -> np.ndarray:
        """Probabilities of being in the ground and excited state of all the nested Results classes.

        Returns:
            np.ndarray: List of probabilities of each executed loop and sequence.
        """

        self._fill_missing_values()

        result_probabilities_df = self._concatenate_acquisition_dataframes()
        expanded_probabilities_df = self._add_meaningful_probabilities_indices(
            result_probabilities_dataframe=result_probabilities_df)
        return self._process_dataframe_if_needed(result_dataframe=expanded_probabilities_df, mean=mean)

    def to_dataframe(self) -> pd.DataFrame:
        """Returns a single dataframe containing the info for the dataframes of all results. In the process, it adds an
        index that specifies to which result belongs the data.

        Returns:
            pd.DataFrame: List of probabilities of each executed loop and sequence.
        """

        result_dataframes = [result.to_dataframe() for result in self.results]
        return pd.concat(result_dataframes, keys=range(len(result_dataframes)), names=['result_index'])

    def _concatenate_acquisition_dataframes(self):
        """ Concatenates the acquisitions from all the results"""
        result_acquisition_list = [result.acquisitions() if result is not None
                                   else pd.DataFrame([]).reindex_like(self.results[0].acquisitions())
                                   for result in self.results]
        return pd.concat(
            result_acquisition_list, keys=range(len(result_acquisition_list)), names=['result_index']).reset_index()

    def _generate_new_acquisitoin_column_names(self):
        """ Checks shape, num_sequence and software_average and returns with that the list of columns that should
         be added to the dataframe. """
        new_columns = [f'loop_index_{i}' for i in range(len(compute_shapes_from_loops(loops=self.loops)))]
        if self.num_sequences > 1:
            new_columns.append('sequence_index')
        if self.software_average > 1:
            new_columns.append('software_avg_index')
        return new_columns

    def _add_meaningful_acquisition_indices(self, result_acquisition_dataframe: pd.DataFrame) -> pd.DataFrame:
        """ Add to the dataframe columns that are relevant indices, computable from the `result_index`, as:
        `loop_index_n` (in case more than one loop is defined), `sequence_index`"""
        old_columns = result_acquisition_dataframe.columns
        new_columns = self._generate_new_acquisitoin_column_names()

        result_acquisition_dataframe[new_columns] = result_acquisition_dataframe.apply(
            lambda row: coordinate_decompose(
                new_dimension_shape=self.shape,
                original_size=len(self.results),
                original_idx=row['result_index']),
            axis=1,
            result_type='expand')
        return result_acquisition_dataframe.reindex(columns=[*new_columns, *old_columns], copy=True)

    def acquisitions(self, mean: bool = False) -> pd.DataFrame:
        """QbloxResult acquisitions of all the nested Results classes.

        Returns:
            np.ndarray: Acquisition values.
        """

        if self.results is None or len(self.results) <= 0:
            return pd.DataFrame([])

        if not isinstance(self.results[0], QbloxResult):
            raise ValueError(f"{type(self.results[0]).__name__} class doesn't have an acquisitions method.")

        self._fill_missing_values()

        result_acquisition_df = self._concatenate_acquisition_dataframes()
        expanded_acquisition_df = self._add_meaningful_acquisition_indices(
            result_acquisition_dataframe=result_acquisition_df)
        return self._process_dataframe_if_needed(result_dataframe=expanded_acquisition_df, mean=mean)

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
