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
from datetime import datetime
from typing import Any, TypedDict

import h5py
import numpy as np


class MeasurementMetadata(TypedDict):
    variables: dict[str, np.ndarray]
    dims: list[list[str]]
    shape: tuple[int, ...]
    shots: int


class QProgramMetadata(TypedDict):
    variables: dict[str, np.ndarray]
    dims: list[list[str]]
    measurements: dict[str, MeasurementMetadata]


class ExperimentMetadata(TypedDict):
    yaml: str
    executed_at: str
    execution_time: float
    qprograms: dict[str, QProgramMetadata]


class ExperimentResults:
    """Manages reading of experiment results from an HDF5 file."""

    QPROGRAMS_PATH = "qprograms"
    MEASUREMENTS_PATH = "measurements"
    RESULTS_PATH = "results"
    VARIABLES_PATH = "variables"
    YAML_PATH = "yaml"
    EXECUTED_AT_PATH = "executed_at"
    EXECUTION_TIME_PATH = "execution_time"

    def __init__(self, path: str):
        self.path = path
        self.results: dict[tuple[str, str], Any] = {}  # To hold the results for in-memory access
        self._file: h5py.File | None = None

    def __enter__(self):
        """Open the HDF5 file for reading."""
        self._file = h5py.File(self.path, mode="r")

        # Prepare access to each results dataset
        for qprogram_name in self._file[ExperimentResults.QPROGRAMS_PATH]:
            qprogram_data = self._file[f"{ExperimentResults.QPROGRAMS_PATH}/{qprogram_name}"]
            for measurement_name in qprogram_data[ExperimentResults.MEASUREMENTS_PATH]:
                self.results[(qprogram_name, measurement_name)] = qprogram_data[
                    f"{ExperimentResults.MEASUREMENTS_PATH}/{measurement_name}/results"
                ]

        return self

    def __exit__(self, *args):
        """Exit the context manager and close the HDF5 file."""
        if self._file is not None:
            self._file.close()

    def __getitem__(self, key: tuple):
        """Get an item from the results dataset.

        Args:
            key (tuple): A tuple of (qprogram_name, measurement_name, *indices).

        Returns:
            float: The value stored in the results dataset at the given indices.
        """
        qprogram_name, measurement_name, *indices = key
        if isinstance(qprogram_name, int):
            qprogram_name = f"QProgram_{qprogram_name}"
        if isinstance(measurement_name, int):
            measurement_name = f"Measurement_{measurement_name}"
        return self.results[(qprogram_name, measurement_name)][tuple(indices)]

    def __len__(self):
        """Get the total number of results datasets."""
        return len(self.results)

    def __iter__(self):
        """Get an iterator over the results datasets."""
        return iter(self.results.items())

    @property
    def yaml(self) -> str:
        """Get the YAML representation of the executed experiment."""
        return self._file[ExperimentResults.YAML_PATH][()]

    @property
    def executed_at(self) -> str:
        """Get the timestamp when execution of the experiment started."""
        return self._file[ExperimentResults.EXECUTED_AT_PATH][()]

    @property
    def execution_time(self) -> float:
        """Get the execution time in seconds."""
        return self._file[ExperimentResults.EXECUTION_TIME_PATH][()]


class ExperimentResultsWriter(ExperimentResults):
    """
    Allows for real-time saving of results from an experiment using the provided metadata information.
    Inherits from `ExperimentResults` to support both read and write operations.
    """

    def __init__(self, metadata: ExperimentMetadata, path: str):
        super().__init__(path)
        self._metadata = metadata

    def _create_results_file(self):
        """Write the prepared structure to an HDF5 file and register loops as dimension scales."""
        h5py.get_config().track_order = True

        with h5py.File(self.path, mode="w") as data_file:
            if ExperimentResults.YAML_PATH in self._metadata:
                data_file[ExperimentResults.YAML_PATH] = self._metadata[ExperimentResults.YAML_PATH]

            if ExperimentResults.EXECUTED_AT_PATH in self._metadata:
                data_file[ExperimentResults.EXECUTED_AT_PATH] = self._metadata[ExperimentResults.EXECUTED_AT_PATH]

            # Create the group for QPrograms
            qprograms_group = data_file.create_group(ExperimentResultsWriter.QPROGRAMS_PATH)

            # Iterate through QPrograms and measurements in the structure
            for qprogram_name, qprogram_data in self._metadata["qprograms"].items():
                qgroup = qprograms_group.create_group(qprogram_name)

                # Write QProgram loops
                qloop_group = qgroup.create_group(ExperimentResults.VARIABLES_PATH)
                for variable in qprogram_data["variables"]:
                    label, values = variable["label"], variable["values"]
                    loop = qloop_group.create_dataset(label, data=values)
                    loop.dims[0].label = label
                    loop.make_scale(label)  # Register as dimension scale

                # Write measurements
                measurement_group = qgroup.create_group(ExperimentResults.MEASUREMENTS_PATH)
                for measurement_name, measurement_data in qprogram_data["measurements"].items():
                    mgroup = measurement_group.create_group(measurement_name)
                    mloop_group = mgroup.create_group(ExperimentResults.VARIABLES_PATH)

                    for variable in measurement_data["variables"]:
                        label, values = variable["label"], variable["values"]
                        loop = mloop_group.create_dataset(label, data=values)
                        loop.dims[0].label = label
                        loop.make_scale(label)  # Register as dimension scale

                    # Create the results dataset
                    results_ds = mgroup.create_dataset(ExperimentResults.RESULTS_PATH, shape=measurement_data["shape"])

                    # Attach dimension scales (loops) to the results dataset
                    for idx, dim_variables in enumerate(qprogram_data["dims"]):
                        for dim_variable in dim_variables:
                            results_ds.dims[idx].attach_scale(qloop_group[dim_variable])
                        results_ds.dims[idx].label = ",".join([dim_variable for dim_variable in dim_variables])
                    for idx, dim_variables in enumerate(measurement_data["dims"]):
                        for dim_variable in dim_variables:
                            results_ds.dims[len(qprogram_data["dims"]) + idx].attach_scale(mloop_group[dim_variable])
                        results_ds.dims[len(qprogram_data["dims"]) + idx].label = ",".join(
                            [dim_variable for dim_variable in dim_variables]
                        )

                    # Attach the extra dimension (usually for I/Q) to the results dataset
                    results_ds.dims[len(qprogram_data["dims"]) + len(measurement_data["dims"])].label = "I/Q"

    def __enter__(self):
        """Open the HDF5 file and create the structure for streaming."""
        self._create_results_file()
        self._file = h5py.File(self.path, mode="a")

        # Prepare access to each results dataset for easy streaming
        for qprogram_name, qprogram_data in self._metadata["qprograms"].items():
            for measurement_name, _ in qprogram_data["measurements"].items():
                self.results[(qprogram_name, measurement_name)] = self._file[
                    f"qprograms/{qprogram_name}/measurements/{measurement_name}/results"
                ]

        return self

    def __setitem__(self, key: tuple, value: float):
        """Set an item in the results dataset."""
        qprogram_name, measurement_name, *indices = key
        if isinstance(qprogram_name, int):
            qprogram_name = f"QProgram_{qprogram_name}"
        if isinstance(measurement_name, int):
            measurement_name = f"Measurement_{measurement_name}"
        self.results[(qprogram_name, measurement_name)][tuple(indices)] = value

    @ExperimentResults.yaml.setter
    def yaml(self, yaml: str):
        """Set the YAML representation of executed experiment."""
        self._file["yaml"] = yaml

    @ExperimentResults.executed_at.setter
    def executed_at(self, dt: datetime):
        """Set the timestamp when execution of the experiment started."""
        self._file["executed_at"] = str(dt)

    @ExperimentResults.execution_time.setter
    def execution_time(self, time: float):
        """Set the execution time in seconds."""
        self._file["execution_time"] = time
