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
from typing import TypedDict

import h5py
import numpy as np

from qililab.result.experiment_results import ExperimentResults


class VariableMetadata(TypedDict):
    """Metadata for a variable used in the experiment.

    Attributes:
        label (str): The label of the variable.
        values (np.ndarray): The array of values for the variable.
    """

    label: str
    values: np.ndarray


class MeasurementMetadata(TypedDict):
    """Metadata for a measurement in the experiment.

    Attributes:
        variables (list[VariableMetadata]): List of variables for the measurement.
        dims (list[list[str]]): Dimensions of the measurement data.
        shape (tuple[int, ...]): Shape of the measurement data.
        shots (int): Number of shots taken for the measurement.
    """

    variables: list[VariableMetadata]
    dims: list[list[str]]
    shape: tuple[int, ...]
    shots: int


class QProgramMetadata(TypedDict):
    """Metadata for a quantum program.

    Attributes:
        variables (dict[str, np.ndarray]): Variables that the QProgram depends upon.
        dims (list[list[str]]): Dimensions of the QProgram data.
        measurements (dict[str, MeasurementMetadata]): Measurements associated with the QProgram.
    """

    variables: dict[str, np.ndarray]
    dims: list[list[str]]
    measurements: dict[str, MeasurementMetadata]


class ExperimentMetadata(TypedDict, total=False):
    """Metadata for an experiment.

    Attributes:
        platform (str): Platform information.
        experiment (str): Experiment description.
        executed_at (datetime): Timestamp when the experiment started execution.
        execution_time (float): Time taken for the execution in seconds.
        qprograms (dict[str, QProgramMetadata]): Quantum programs included in the experiment.
    """

    platform: str
    experiment: str
    executed_at: datetime
    execution_time: float
    qprograms: dict[str, QProgramMetadata]


class ExperimentResultsWriter(ExperimentResults):
    """
    Allows for real-time saving of results from an experiment using the provided metadata information.

    Inherits from `ExperimentResults` to support both read and write operations.
    """

    def __init__(self, path: str, metadata: ExperimentMetadata):
        """Initializes the ExperimentResultsWriter instance.

        Args:
            path (str): The file path to save the HDF5 results file.
            metadata (ExperimentMetadata): The metadata describing the experiment structure.
        """
        super().__init__(path)
        self._metadata = metadata

    # pylint: disable=too-many-locals
    def _create_results_file(self):
        """Creates the HDF5 file structure and registers loops as dimension scales.

        Writes the metadata to the HDF5 file and sets up the datasets and groups for streaming data.
        """
        h5py.get_config().track_order = True

        if "platform" in self._metadata:
            self.platform = self._metadata["platform"]

        if "experiment" in self._metadata:
            self.experiment = self._metadata["experiment"]

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

                # Write variables that QProgram depends upon (software loops)
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

                    # Write shots of measurement
                    mgroup["shots"] = measurement_data["shots"]

                    # Write variables that measurement depends upon (hardware loops)
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
                        results_ds.dims[idx].label = ",".join(list(dim_variables))
                    for idx, dim_variables in enumerate(measurement_data["dims"]):
                        for dim_variable in dim_variables:
                            results_ds.dims[len(qprogram_data["dims"]) + idx].attach_scale(mloop_group[dim_variable])
                        results_ds.dims[len(qprogram_data["dims"]) + idx].label = ",".join(list(dim_variables))

                    # Attach the extra dimension (usually for I/Q) to the results dataset
                    results_ds.dims[len(qprogram_data["dims"]) + len(measurement_data["dims"])].label = "I/Q"

    def _create_resuts_access(self):
        """Sets up internal data structures to allow for real-time data writing to the HDF5 file."""
        if "qprograms" in self._metadata:
            for qprogram_name, qprogram_data in self._metadata["qprograms"].items():
                for measurement_name, _ in qprogram_data["measurements"].items():
                    self.data[qprogram_name, measurement_name] = self._file[
                        f"qprograms/{qprogram_name}/measurements/{measurement_name}/results"
                    ]

    def __enter__(self):
        """Opens the HDF5 file and creates the structure for streaming.

        Returns:
            ExperimentResultsWriter: The ExperimentResultsWriter instance.
        """
        self._file = h5py.File(self.path, mode="w")
        self._create_results_file()
        self._create_resuts_access()

        return self

    def __setitem__(self, key: tuple, value: float):
        """Sets an item in the results dataset.

        Args:
            key (tuple): A tuple of (qprogram_name or index, measurement_name or index, *indices).
            value (float): The value to set at the specified indices.
        """
        qprogram_name, measurement_name, *indices = key
        if isinstance(qprogram_name, int):
            qprogram_name = f"QProgram_{qprogram_name}"
        if isinstance(measurement_name, int):
            measurement_name = f"Measurement_{measurement_name}"
        self.data[qprogram_name, measurement_name][tuple(indices)] = value

    @ExperimentResults.platform.setter
    def platform(self, platform: str):
        """Sets the YAML representation of the platform.

        Args:
            platform (str): The YAML string representing the platform.
        """
        path = ExperimentResults.PLATFORM_PATH
        if path in self._file:
            del self._file[path]
        self._file[path] = platform

    @ExperimentResults.experiment.setter
    def experiment(self, experiment: str):
        """Sets the YAML representation of the executed experiment.

        Args:
            experiment (str): The YAML string representing the experiment.
        """
        path = ExperimentResults.EXPERIMENT_PATH
        if path in self._file:
            del self._file[path]
        self._file[path] = experiment

    @ExperimentResults.executed_at.setter
    def executed_at(self, dt: datetime):
        """Sets the timestamp when execution of the experiment started.

        Args:
            dt (datetime): The datetime when execution started.
        """
        path = ExperimentResults.EXECUTED_AT_PATH
        if path in self._file:
            del self._file[path]
        self._file[path] = dt.strftime("%Y-%m-%d %H:%M:%S")

    @ExperimentResults.execution_time.setter
    def execution_time(self, time: float):
        """Sets the execution time in seconds.

        Args:
            time (float): The execution time in seconds.
        """
        path = ExperimentResults.EXECUTION_TIME_PATH
        if path in self._file:
            del self._file[path]
        self._file[path] = str(time)
