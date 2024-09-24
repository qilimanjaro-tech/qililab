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
import matplotlib.pyplot as plt
import numpy as np


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


class ExperimentResults:
    """Provides methods to access the experiment results stored in an HDF5 file."""

    QPROGRAMS_PATH = "qprograms"
    MEASUREMENTS_PATH = "measurements"
    RESULTS_PATH = "results"
    VARIABLES_PATH = "variables"
    EXPERIMENT_PATH = "experiment"
    PLATFORM_PATH = "platform"
    EXECUTED_AT_PATH = "executed_at"
    EXECUTION_TIME_PATH = "execution_time"

    def __init__(self, path: str):
        """Initializes the ExperimentResults instance.

        Args:
            path (str): The file path to the HDF5 results file.
        """
        self.path = path
        self.data: dict[tuple[str, str], Any] = {}  # To hold links to the data of the results for in-memory access
        self.dimensions: dict[
            tuple[str, str], Any
        ] = {}  # To hold links to dimensions of the results for in-memory access
        self._file: h5py.File

    def __enter__(self):
        """Opens the HDF5 file for reading.

        Returns:
            ExperimentResults: The ExperimentResults instance.
        """
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

    def get(self, qprogram: int | str = 0, measurement: int | str = 0):
        """Retrieves data and dimensions for a specified quantum program and measurement.

        Args:
            qprogram (int | str, optional): The index or name of the quantum program. Defaults to 0.
            measurement (int | str, optional): The index or name of the measurement. Defaults to 0.

        Returns:
            tuple[np.ndarray, list[dict]]: A tuple containing the data array and a list of dimension dictionaries.
        """
        if isinstance(qprogram, int):
            qprogram = f"QProgram_{qprogram}"
        if isinstance(measurement, int):
            measurement = f"Measurement_{measurement}"

        data = self.data[(qprogram, measurement)][()]
        dims = [
            {"labels": dim.label.split(","), "values": [values[()] for values in dim.values()]}
            for dim in self.dimensions[(qprogram, measurement)]
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
        """Gets the total number of results datasets.

        Returns:
            int: The number of results datasets.
        """
        return len(self.data)

    def __iter__(self):
        """Gets an iterator over the results datasets.

        Returns:
            Iterator: An iterator over the results datasets.
        """
        return iter(self.data.items())

    @property
    def experiment(self) -> str:
        """Gets the YAML representation of the executed experiment.

        Returns:
            str: The YAML string of the executed experiment.
        """
        return self._file[ExperimentResults.EXPERIMENT_PATH][()].decode("utf-8")  # type: ignore[index]

    @property
    def platform(self) -> str:
        """Gets the YAML representation of the platform.

        Returns:
            str: The YAML string of the platform.
        """
        return self._file[ExperimentResults.PLATFORM_PATH][()].decode("utf-8")

    @property
    def executed_at(self) -> datetime:
        """Gets the timestamp when execution of the experiment started.

        Returns:
            datetime: The timestamp of when the experiment started.
        """
        return datetime.strptime(
            self._file[ExperimentResults.EXECUTED_AT_PATH][()].decode("utf-8"), "%Y-%m-%d %H:%M:%S"
        )

    @property
    def execution_time(self) -> float:
        """Gets the execution time in seconds.

        Returns:
            float: The execution time in seconds.
        """
        return float(self._file[ExperimentResults.EXECUTION_TIME_PATH][()].decode("utf-8"))

    # pylint: disable=too-many-statements
    def plot_S21(self, qprogram: int | str = 0, measurement: int | str = 0):
        """Plots the S21 parameter from the experiment results.

        Args:
            qprogram (int | str, optional): The index or name of the quantum program. Defaults to 0.
            measurement (int | str, optional): The index or name of the measurement. Defaults to 0.

        Raises:
            NotImplementedError: If the data has more than 2 dimensions.
        """

        def decibels(s21: np.ndarray):
            """Convert result values from s21 into dB"""
            return 20 * np.log10(np.abs(s21))

        def plot_1d(s21: np.ndarray, dims):
            """Plot 1d"""
            x_labels, x_values = dims[0]["labels"], dims[0]["values"]

            _, ax1 = plt.subplots()
            ax1.set_title(self.path)
            ax1.set_xlabel(x_labels[0])
            ax1.set_ylabel(r"$|S_{21}|$")
            ax1.plot(x_values[0], s21, ".")

            if len(x_labels) > 1:
                # Create secondary x-axis
                ax2 = ax1.twiny()

                # Set labels
                ax2.set_xlabel(x_labels[1])
                ax2.set_xlim(min(x_values[1]), max(x_values[1]))

                # Set tick locations
                ax2_ticks = np.linspace(min(x_values[1]), max(x_values[1]), num=6)
                ax2.set_xticks(ax2_ticks)

                # Force scientific notation
                ax2.ticklabel_format(axis="x", style="sci", scilimits=(-3, 3))

            plt.show()

        # pylint: disable=too-many-locals
        def plot_2d(s21: np.ndarray, dims):
            """Plot 2d"""
            x_labels, x_values = dims[0]["labels"], dims[0]["values"]
            y_labels, y_values = dims[1]["labels"], dims[1]["values"]

            # Create x and y edge arrays by extrapolating the edges
            x_edges = np.linspace(x_values[0].min(), x_values[0].max(), len(x_values[0]) + 1)
            y_edges = np.linspace(y_values[0].min(), y_values[0].max(), len(y_values[0]) + 1)

            fig, ax1 = plt.subplots()
            ax1.set_title(self.path)
            ax1.set_xlabel(x_labels[0])
            ax1.set_ylabel(y_labels[0])

            # Force scientific notation
            ax1.ticklabel_format(axis="both", style="sci", scilimits=(-3, 3))

            mesh = ax1.pcolormesh(x_edges, y_edges, s21.T, cmap="viridis", shading="auto")
            fig.colorbar(mesh, ax=ax1)

            if len(x_labels) > 1:
                # Create secondary x-axis
                ax2 = ax1.twiny()

                # Set labels
                ax2.set_xlabel(x_labels[1])
                ax2.set_xlim(min(x_values[1]), max(x_values[1]))

                # Set tick locations
                ax2_ticks = np.linspace(min(x_values[1]), max(x_values[1]), num=6)
                ax2.set_xticks(ax2_ticks)

                # Force scientific notation
                ax2.ticklabel_format(axis="x", style="sci", scilimits=(-3, 3))
            if len(y_labels) > 1:
                ax3 = ax1.twinx()
                ax3.set_ylabel(y_labels[1])
                ax3.set_ylim(min(y_values[1]), max(y_values[1]))

                # Set tick locations
                ax3_ticks = np.linspace(min(y_values[1]), max(y_values[1]), num=6)
                ax3.set_xticks(ax3_ticks)

                # Force scientific notation
                ax3.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))

            plt.tight_layout()
            plt.show()

        data, dims = self.get(qprogram=qprogram, measurement=measurement)

        # Calculate S21
        s21 = data[:, 0] + 1j * data[:, 1]
        s21 = decibels(s21)

        n_dimensions = len(s21.shape)
        if n_dimensions == 1:
            plot_1d(data, dims)
        elif n_dimensions == 2:
            plot_2d(data, dims)
        else:
            raise NotImplementedError("3D and higher dimension plots are not supported yet.")


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
                    self.data[(qprogram_name, measurement_name)] = self._file[
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
        self.data[(qprogram_name, measurement_name)][tuple(indices)] = value

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
