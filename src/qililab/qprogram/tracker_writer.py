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
# mypy: disable-error-code="attr-defined"
import os
from datetime import datetime
from typing import TypedDict

import h5py

from qililab.result.experiment_results import ExperimentResults
from qililab.result.experiment_results_writer import VariableMetadata


class BlockMetadata(TypedDict):
    """Metadata for a measurement in the experiment.

    Attributes:
        variables (list[VariableMetadata]): List of variables for the measurement.
        dims (list[list[str]]): Dimensions of the measurement data.
        shape (tuple[int, ...]): Shape of the measurement data.
        shots (int): Number of shots taken for the measurement.
    """

    alias: list[str]
    real_path: dict[str, list]
    guessed_path: dict[str, list]
    windows: dict[str, list]
    total_data: dict[str, list]
    experiment_dims: dict[str, list]


class TrackerMetadata(TypedDict):
    """Metadata for an experiment.

    Attributes:
        executed_at (datetime): Timestamp when the experiment started execution.
        execution_time (float): Time taken for the execution in seconds.
    """

    executed_at: datetime
    execution_time: float
    values: VariableMetadata
    experiments: BlockMetadata


class TrackerWriter:
    """
    Allows for real-time saving of results from an experiment using the provided metadata information.

    Inherits from `ExperimentResults` to support both read and write operations.
    """

    def __init__(self, path: str, metadata: TrackerMetadata):
        """Initializes the ExperimentResultsWriter instance.

        Args:
            path (str): The file path to save the HDF5 results file.
            metadata (ExperimentMetadata): The metadata describing the experiment structure.
        """
        self.path: str = path
        self._metadata = metadata
        self.experiment_path: dict[str, dict] = {}
        self.windows: dict[str, h5py.Group] = {}
        self.guess: dict[str, h5py.Group] = {}
        self.data: dict[str, h5py.Group] = {}
        self.real: dict[str, h5py.Group] = {}

    def __enter__(self):
        """Opens the HDF5 file and creates the structure for streaming.

        Returns:
            ExperimentResultsWriter: The ExperimentResultsWriter instance.
        """
        self.path = self._create_results_path(self._metadata["executed_at"])
        self._create_experiment_path()
        self._tracker_file = h5py.File(f"{self.path}/tracker_data.h5", mode="w")
        self._create_results_access()
        self._create_file()

        return self

    def set(self, alias, window, guess_path, data, real_path):
        """Sets an item in the results dataset.

        Args:
            key (tuple): A tuple of (qprogram_name or index, measurement_name or index, *indices).
            value (float): The value to set at the specified indices.
        """

        self.windows[alias] = window
        self.guess[alias] = guess_path
        self.data[alias] = data
        self.real[alias] = real_path

    def _create_results_path(self, executed_at: datetime):
        # Format date and time for directory names
        date = executed_at.strftime("%Y%m%d")
        timestamp = executed_at.strftime("%H%M%S")

        # Format the path based on the path's format
        time_path = f"/{date}/{timestamp}"

        # Construct the full path
        path_file = os.path.join(self.path, time_path)

        # Ensure it is an absolute path
        path_file = os.path.abspath(path_file)

        # Create the directories if they don't exist
        os.makedirs(os.path.dirname(path_file), exist_ok=True)

        return path_file

    # pylint: disable=too-many-locals
    def _create_file(self):
        """Creates the HDF5 file structure and registers loops as dimension scales.

        Writes the metadata to the HDF5 file and sets up the datasets and groups for streaming data.
        """
        h5py.get_config().track_order = True

        if "executed_at" in self._metadata:
            self.executed_at = self._metadata["executed_at"]

        if "execution_time" in self._metadata:
            self.execution_time = self._metadata["execution_time"]

        if "values" in self._metadata and "experiment" in self._metadata:
            value_name, value_value = self._metadata["values"].items()
            valuegroup = self._tracker_file.create_group("Values")
            loop = valuegroup.create_dataset(f"{value_name}", data=value_value)
            loop.dims[0].label = value_name
            loop.make_scale(value_name)  # Register as dimension scale

            for block_alias in self._metadata["experiments"]["alias"]:
                blockgroup = self._tracker_file.create_group(block_alias)

                windows_results = blockgroup.create_dataset("windows")
                guessed_results = blockgroup.create_dataset("guessed path")
                data_results = blockgroup.create_dataset("data")
                real_results = blockgroup.create_dataset("real path")

                windows_results.dims[0].attach_scale(valuegroup[value_name])
                windows_results.dims[0].label = value_name

                guessed_results.dims[0].attach_scale(valuegroup[value_name])
                guessed_results.dims[0].label = value_name

                data_results.dims[0].attach_scale(valuegroup[value_name])
                data_results.dims[0].label = value_name

                real_results.dims[0].attach_scale(valuegroup[value_name])
                real_results.dims[0].label = value_name

    def _create_experiment_path(self):
        for alias in self._metadata["experiments"]["alias"]:
            self.experiment_path[alias] = {}
            os.makedirs(f"{self.path}/{alias}", exist_ok=True)
            for value in self._metadata["experiments"]["values"]:
                os.makedirs(f"{self.path}/{alias}/{value['label']}_{value['values']}", exist_ok=True)
                self.experiment_path[alias][value["values"]] = f"{self.path}/{alias}/{value['label']}_{value['values']}"

    def _create_results_access(self):
        """Sets up internal data structures to allow for real-time data writing to the HDF5 file."""
        if "experiments" in self._metadata:
            for alias in self._metadata["experiments"]["alias"]:
                self.windows[alias] = self._tracker_file[f"{alias}/windows"]
                self.guess[alias] = self._tracker_file[f"{alias}/guessed path"]
                self.data[alias] = self._tracker_file[f"{alias}/data"]
                self.real[alias] = self._tracker_file[f"{alias}/real path"]

    @ExperimentResults.executed_at.setter
    def executed_at(self, dt: datetime):
        """Sets the timestamp when execution of the experiment started.

        Args:
            dt (datetime): The datetime when execution started.
        """
        path = "executed_at"
        if path in self._tracker_file:
            del self._tracker_file[path]
        self._tracker_file[path] = dt.strftime("%Y-%m-%d %H:%M:%S")

    @ExperimentResults.execution_time.setter
    def execution_time(self, time: float):
        """Sets the execution time in seconds.

        Args:
            time (float): The execution time in seconds.
        """
        path = "execution_time"
        if path in self._tracker_file:
            del self._tracker_file[path]
        self._tracker_file[path] = str(time)
