# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Results class."""
from copy import deepcopy
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from qililab.constants import EXPERIMENT, RESULTSDATAFRAME, RUNCARD
from qililab.utils import coordinate_decompose
from qililab.utils.dataframe_manipulation import concatenate_creating_new_name_index
from qililab.utils.factory import Factory
from qililab.utils.loop import Loop
from qililab.utils.util_loops import compute_ranges_from_loops, compute_shapes_from_loops

from .counts import Counts
from .qblox_results.qblox_result import QbloxResult
from .result import Result


@dataclass
class Results:
    """Results class."""

    software_average: int
    num_schedules: int
    loops: list[Loop] | None = None
    shape: list[int] = field(default_factory=list)
    results: list[Result] = field(default_factory=list)
    _computed_dataframe_indices: list[str] = field(init=False, default_factory=list)
    _data_dataframe_indices: set[str] = field(init=False, default_factory=set)

    def __post_init__(self):
        """Add num_schedules to shape."""
        if not self.shape:
            self.shape = compute_shapes_from_loops(loops=self.loops)
        if self.num_schedules > 1:
            self.shape.append(self.num_schedules)
        if self.software_average > 1:
            self.shape.append(self.software_average)
        if self.results and isinstance(self.results[0], dict):
            tmp_results = deepcopy(self.results)
            # Pop the result name (qblox, ...) from the dictionary and instantiate its corresponding Result class.
            self.results = [Factory.get(result.pop(RUNCARD.NAME))(**result) for result in tmp_results]
        if self.loops is not None and isinstance(self.loops[0], dict):
            self.loops = [Loop(**loop) for loop in self.loops]

    def add(self, result: Result):
        """Append an ExecutionResults object.

        Args:
            result (Result): Result object.
        """
        self.results.append(result)

    def probabilities(self) -> dict[str, float]:
        """Probabilities of being in the ground and excited state of all the nested Results classes.

        Returns:
            dict[str, float]: Dictionary containing the probabilities (value) of being measured in each state (key).
        """
        return self._counts_object().probabilities()

    def counts(self):
        """Returns the counts dictionary containing the number of measurements (counts) of each state.

        Returns:
            dict[str, int]: Dictionary containing the number of measurements (value) in each state (key).
        """
        return self._counts_object().as_dict()

    def _counts_object(self) -> Counts:
        """Returns a Counts object containing the number of measurements (counts) of each state.

        Returns:
            Counts: Counts object containing the number of measurements (counts) of each state.
        """
        if len(self.results) == 0:
            return Counts(n_qubits=0)
        n_qubits = self.results[0].counts_object().n_qubits
        all_counts = Counts(n_qubits=n_qubits)
        for result in self.results:
            all_counts += result.counts_object()
        return all_counts

    def to_dataframe(self) -> pd.DataFrame:
        """Returns a single dataframe containing the info for the dataframes of all results. In the process, it adds an
        index that specifies to which result belongs the data.

        Returns:
            pd.DataFrame: List of probabilities of each executed loop and sequence.
        """

        result_dataframes = [result.to_dataframe() for result in self.results]
        return concatenate_creating_new_name_index(dataframe_list=result_dataframes, new_index_name="result_index")

    def _build_empty_result_dataframe(self):
        """Builds an empty result dataframe, with the minimal number of columns and nans as values"""
        return pd.DataFrame(
            [[np.nan] * len(self._data_dataframe_indices)],
            columns=pd.Index(self._data_dataframe_indices).transpose(),
            index=[0],
        ).reset_index(drop=True)

    def _concatenate_acquisition_dataframes(self):
        """Concatenates the acquisitions from all the results"""
        self._data_dataframe_indices = set().union(
            *[result.data_dataframe_indices for result in self.results if result is not None]
        )
        result_acquisition_list = [
            result.acquisitions().reset_index(drop=True) if result is not None else self._build_empty_result_dataframe()
            for result in self.results
        ]
        return concatenate_creating_new_name_index(
            dataframe_list=result_acquisition_list, new_index_name=RESULTSDATAFRAME.RESULTS_INDEX
        )

    def _generate_new_acquisition_column_names(self):
        """Checks shape, num_sequence and software_average and returns with that the list of columns that should
        be added to the dataframe."""
        new_columns = [
            f"{RESULTSDATAFRAME.LOOP_INDEX}{i}" for i in range(len(compute_shapes_from_loops(loops=self.loops)))
        ]
        if self.num_schedules > 1:
            new_columns.append(RESULTSDATAFRAME.SEQUENCE_INDEX)
        if self.software_average > 1:
            new_columns.append(RESULTSDATAFRAME.SOFTWARE_AVG_INDEX)
        return new_columns

    def _add_meaningful_acquisition_indices(self, result_acquisition_dataframe: pd.DataFrame) -> pd.DataFrame:
        """Add to the dataframe columns that are relevant indices, computable from the `result_index`, as:
        `loop_index_n` (in case more than one loop is defined), `sequence_index`"""
        old_columns = result_acquisition_dataframe.columns
        self._computed_dataframe_indices = self._generate_new_acquisition_column_names()
        self._data_dataframe_indices = set().union(
            *[result.data_dataframe_indices for result in self.results if result is not None]
        )

        result_acquisition_dataframe[self._computed_dataframe_indices] = result_acquisition_dataframe.apply(
            lambda row: coordinate_decompose(
                new_dimension_shape=self.shape,
                original_size=len(self.results),
                original_idx=row[RESULTSDATAFRAME.RESULTS_INDEX],
            ),
            axis=1,
            result_type="expand",
        )
        return result_acquisition_dataframe.reindex(
            columns=[*self._computed_dataframe_indices, *old_columns], copy=True
        )

    def _process_acquisition_dataframe_if_needed(
        self, result_dataframe: pd.DataFrame, mean: bool = False
    ) -> pd.DataFrame:
        """Process the dataframe by applying software average if required"""

        if mean and self.software_average > 1:
            preserved_columns = [
                col
                for col in result_dataframe.columns.values
                if col
                not in self._data_dataframe_indices.union(
                    {RESULTSDATAFRAME.RESULTS_INDEX, RESULTSDATAFRAME.SOFTWARE_AVG_INDEX}
                )
            ]
            groups_to_average = result_dataframe.groupby(preserved_columns)
            averaged_df = groups_to_average.mean().reset_index()
            averaged_df[RESULTSDATAFRAME.RESULTS_INDEX] = groups_to_average.first().reset_index()[
                RESULTSDATAFRAME.RESULTS_INDEX
            ]
            averaged_df.drop(columns=RESULTSDATAFRAME.SOFTWARE_AVG_INDEX, inplace=True)
            result_dataframe = averaged_df

        return result_dataframe

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
            result_acquisition_dataframe=result_acquisition_df
        )
        return self._process_acquisition_dataframe_if_needed(result_dataframe=expanded_acquisition_df, mean=mean)

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
            EXPERIMENT.NUM_SCHEDULES: self.num_schedules,
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
