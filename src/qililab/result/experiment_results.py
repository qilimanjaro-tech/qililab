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


class VariableMetadata(TypedDict):
    label: str
    values: np.ndarray


class MeasurementMetadata(TypedDict):
    variables: list[VariableMetadata]
    dims: list[list[str]]
    shape: tuple[int, ...]
    shots: int


class QProgramMetadata(TypedDict):
    variables: dict[str, np.ndarray]
    dims: list[list[str]]
    measurements: dict[str, MeasurementMetadata]


class ExperimentMetadata(TypedDict, total=False):
    yaml: str
    executed_at: datetime
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
        self.data: dict[tuple[str, str], Any] = {}  # To hold links to the data of the results for in-memory access
        self.dimensions: dict[
            tuple[str, str], Any
        ] = {}  # To hold links to dimensions of the results for in-memory access
        self._file: h5py.File | None = None

    def __enter__(self):
        """Open the HDF5 file for reading."""
        self._file = h5py.File(self.path, mode="r")

        # Prepare access to each results dataset and its dimensions
        for qprogram_name in self._file[ExperimentResults.QPROGRAMS_PATH]:
            qprogram_data = self._file[f"{ExperimentResults.QPROGRAMS_PATH}/{qprogram_name}"]
            for measurement_name in qprogram_data[ExperimentResults.MEASUREMENTS_PATH]:
                self.data[(qprogram_name, measurement_name)] = qprogram_data[
                    f"{ExperimentResults.MEASUREMENTS_PATH}/{measurement_name}/results"
                ]
                # Store the dimensions
                self.dimensions[(qprogram_name, measurement_name)] = qprogram_data[
                    f"{ExperimentResults.MEASUREMENTS_PATH}/{measurement_name}/results"
                ].dims

        return self

    def __exit__(self, *args):
        """Exit the context manager and close the HDF5 file."""
        if self._file is not None:
            self._file.close()

    def get(self, qprogram: int | str, measurement: int | str):
        if isinstance(qprogram, int):
            qprogram = f"QProgram_{qprogram}"
        if isinstance(measurement, int):
            measurement = f"Measurement_{measurement}"

        data = self.data[(qprogram, measurement)][()]
        dims = [
            (dim.label, [values[()] for values in dim.values()]) for dim in self.dimensions[(qprogram, measurement)]
        ]

        return data, dims

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
        return self.data[(qprogram_name, measurement_name)][tuple(indices)]

    def __len__(self):
        """Get the total number of results datasets."""
        return len(self.data)

    def __iter__(self):
        """Get an iterator over the results datasets."""
        return iter(self.data.items())

    @property
    def yaml(self) -> str:
        """Get the YAML representation of the executed experiment."""
        return self._file[ExperimentResults.YAML_PATH][()].decode("utf-8")

    @property
    def executed_at(self) -> datetime:
        """Get the timestamp when execution of the experiment started."""
        return datetime.strptime(
            self._file[ExperimentResults.EXECUTED_AT_PATH][()].decode("utf-8"), "%Y-%m-%dT%H:%M:%S"
        )

    @property
    def execution_time(self) -> float:
        """Get the execution time in seconds."""
        return float(self._file[ExperimentResults.EXECUTION_TIME_PATH][()].decode("utf-8"))


class ExperimentResultsWriter(ExperimentResults):
    """
    Allows for real-time saving of results from an experiment using the provided metadata information.
    Inherits from `ExperimentResults` to support both read and write operations.
    """

    def __init__(self, path: str, metadata: ExperimentMetadata):
        super().__init__(path)
        self._metadata = metadata

    def _create_results_file(self):
        """Write the prepared structure to an HDF5 file and register loops as dimension scales."""
        h5py.get_config().track_order = True

        if "yaml" in self._metadata:
            self.yaml = self._metadata["yaml"]

        if "executed_at" in self._metadata:
            self.executed_at = self._metadata["executed_at"]

        if "execution_time" in self._metadata:
            self.execution_time = self._metadata["execution_time"]

        if "qprograms" in self._metadata:
            # Create the group for QPrograms
            qprograms_group = self._file.create_group(ExperimentResultsWriter.QPROGRAMS_PATH)

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

    def _create_resuts_access(self):
        # Prepare access to each results dataset for easy streaming
        if "qprograms" in self._metadata:
            for qprogram_name, qprogram_data in self._metadata["qprograms"].items():
                for measurement_name, _ in qprogram_data["measurements"].items():
                    self.data[(qprogram_name, measurement_name)] = self._file[
                        f"qprograms/{qprogram_name}/measurements/{measurement_name}/results"
                    ]

    def __enter__(self):
        """Open the HDF5 file and create the structure for streaming."""
        self._file = h5py.File(self.path, mode="w")
        self._create_results_file()
        self._create_resuts_access()

        return self

    def __setitem__(self, key: tuple, value: float):
        """Set an item in the results dataset."""
        qprogram_name, measurement_name, *indices = key
        if isinstance(qprogram_name, int):
            qprogram_name = f"QProgram_{qprogram_name}"
        if isinstance(measurement_name, int):
            measurement_name = f"Measurement_{measurement_name}"
        self.data[(qprogram_name, measurement_name)][tuple(indices)] = value

    @ExperimentResults.yaml.setter
    def yaml(self, yaml: str):
        """Set the YAML representation of executed experiment."""
        path = ExperimentResults.YAML_PATH
        if path in self._file:
            del self._file[path]
        self._file[path] = yaml

    @ExperimentResults.executed_at.setter
    def executed_at(self, dt: datetime):
        """Set the timestamp when execution of the experiment started."""
        path = ExperimentResults.EXECUTED_AT_PATH
        if path in self._file:
            del self._file[path]
        self._file[path] = str(dt)

    @ExperimentResults.execution_time.setter
    def execution_time(self, time: float):
        """Set the execution time in seconds."""
        path = ExperimentResults.EXECUTION_TIME_PATH
        if path in self._file:
            del self._file[path]
        self._file[path] = str(time)
