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
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import h5py
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class DimensionInfo:
    """Dataclass to store information of a Variable"""

    labels: list[str]
    values: list[np.ndarray]


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

    S21_PLOT_NAME = "S21.png"

    def __init__(self, path: str):
        """Initializes the ExperimentResults instance.

        Args:
            path (str): The file path to the HDF5 results file.
            slurm_execution (bool): Flag that defines if the liveplot will be held through Dash or a notebook cell. Defaults to True.
        """
        self.path = path
        self.data: dict[tuple[str, str], Any] = {}  # To hold links to the data of the results for in-memory access
        # To hold links to dimensions of the results for in-memory access
        self.dimensions: dict[tuple[str, str], Any] = {}
        self._file: h5py.File

    def __enter__(self):
        """Opens the HDF5 file for reading.

        Returns:
            ExperimentResults: The ExperimentResults instance.
        """
        self._file = h5py.File(self.path, mode="r", libver="latest")

        # Prepare access to each results dataset and its dimensions
        for qprogram_name in self._file[ExperimentResults.QPROGRAMS_PATH]:
            qprogram_data = self._file[f"{ExperimentResults.QPROGRAMS_PATH}/{qprogram_name}"]
            for measurement_name in qprogram_data[ExperimentResults.MEASUREMENTS_PATH]:
                self.data[qprogram_name, measurement_name] = qprogram_data[
                    f"{ExperimentResults.MEASUREMENTS_PATH}/{measurement_name}/results"
                ]
                # Store the dimensions
                self.dimensions[qprogram_name, measurement_name] = qprogram_data[
                    f"{ExperimentResults.MEASUREMENTS_PATH}/{measurement_name}/results"
                ].dims

        return self

    def __exit__(self, *_):
        """Exit the context manager and close the HDF5 file."""
        if self._file is not None:
            self._file.close()

    def get(self, qprogram: int | str = 0, measurement: int | str = 0) -> tuple[np.ndarray, list[DimensionInfo]]:
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

        data = self.data[qprogram, measurement][()]
        dims = [
            DimensionInfo(labels=dim.label.split(","), values=[values[()] for values in dim.values()])
            for dim in self.dimensions[qprogram, measurement]
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
        return self.data[qprogram_name, measurement_name][tuple(indices)]

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
    def plot_S21(self, qprogram: int | str = 0, measurement: int | str = 0, save_plot: bool = True):
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

        def plot_1d(s21: np.ndarray, dims: list[DimensionInfo]):
            """Plot 1d"""
            x_labels, x_values = dims[0].labels, dims[0].values

            fig, ax1 = plt.subplots()
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

            if save_plot:
                folder = os.path.dirname(self.path)
                path = os.path.join(folder, ExperimentResults.S21_PLOT_NAME)
                fig.savefig(path)

            plt.show()

        # pylint: disable=too-many-locals
        def plot_2d(s21: np.ndarray, dims):
            """Plot 2d"""
            x_labels, x_values = dims[0].labels, dims[0].values
            y_labels, y_values = dims[1].labels, dims[1].values

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

            if save_plot:
                folder = os.path.dirname(self.path)
                path = os.path.join(folder, "S21.png")
                fig.savefig(path)

            plt.tight_layout()
            plt.show()

        data, dims = self.get(qprogram=qprogram, measurement=measurement)

        # Calculate S21
        s21 = data[..., 0] + 1j * data[..., 1]
        s21 = decibels(s21)

        n_dimensions = len(s21.shape)
        if n_dimensions == 1:
            plot_1d(s21, dims)
        elif n_dimensions == 2:
            plot_2d(s21, dims)
        else:
            raise NotImplementedError("3D and higher dimension plots are not supported yet.")
