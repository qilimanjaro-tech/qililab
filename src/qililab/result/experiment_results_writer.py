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
from datetime import datetime
from typing import Any

import h5py
import numpy as np


class ExperimentResultsWriter:
    """
    Allows for real-time saving of results from an experiment using the provided structure.

    This class manages the experiment's loops and results, writing them to an HDF5 file with proper dimension scales.

    Args:
        structure (dict): The nested dictionary representing the experiment structure, loops, and measurements.
        path (str): The path to the HDF5 file to save results.
    """

    QPROGRAMS_PATH = "qprograms"
    MEASUREMENTS_PATH = "measurements"
    RESULTS_PATH = "results"
    YAML_PATH = "yaml"
    EXECUTED_AT_PATH = "executed_at"
    EXECUTION_TIME_PATH = "execution_time"

    def __init__(self, structure: dict, path: str):
        self.structure = structure
        self.path = path
        self.results: dict[tuple[str, str], Any] = {}  # To hold the results for in-memory access
        self._file: h5py.File | None = None

    def _create_results_file(self):
        """Write the prepared structure to an HDF5 file and register loops as dimension scales."""
        h5py.get_config().track_order = True

        with h5py.File(self.path, mode="w") as data_file:
            if ExperimentResultsWriter.YAML_PATH in self.structure:
                data_file[ExperimentResultsWriter.YAML_PATH] = self.structure[ExperimentResultsWriter.YAML_PATH]

            if ExperimentResultsWriter.EXECUTED_AT_PATH in self.structure:
                data_file[ExperimentResultsWriter.EXECUTED_AT_PATH] = self.structure[
                    ExperimentResultsWriter.EXECUTED_AT_PATH
                ]

            # Create the group for QPrograms
            qprogram_group = data_file.create_group(ExperimentResultsWriter.QPROGRAMS_PATH)

            # Iterate through QPrograms and measurements in the structure
            for qprogram_name, qprogram_data in self.structure["qprograms"].items():
                qgroup = qprogram_group.create_group(qprogram_name)

                # Write QProgram loops
                qloop_group = qgroup.create_group("loops")
                for loop_label, loop_values in qprogram_data["loops"].items():
                    loop = qloop_group.create_dataset(loop_label, data=loop_values)
                    loop.dims[0].label = loop_label
                    loop.make_scale(loop_label)  # Register as dimension scale

                # Write measurements
                measurement_group = qgroup.create_group("measurements")
                for measurement_name, measurement_data in qprogram_data["measurements"].items():
                    mgroup = measurement_group.create_group(measurement_name)
                    mloop_group = mgroup.create_group("loops")

                    for loop_label, loop_values in measurement_data["loops"].items():
                        loop = mloop_group.create_dataset(loop_label, data=loop_values)
                        loop.dims[0].label = loop_label
                        loop.make_scale(loop_label)  # Register as dimension scale

                    # Create the results dataset
                    results_ds = mgroup.create_dataset("results", shape=measurement_data["shape"])

                    # Attach dimension scales (loops) to the results dataset
                    for idx, (loop_label, loop_value) in enumerate(qloop_group.items()):
                        results_ds.dims[idx].attach_scale(loop_value)
                        results_ds.dims[idx].label = loop_label
                    for idx, (loop_label, loop_value) in enumerate(mloop_group.items()):
                        results_ds.dims[len(qloop_group) + idx].attach_scale(loop_value)
                        results_ds.dims[len(qloop_group) + idx].label = loop_label

                    # Attach the extra dimension (usually for I/Q) to the results dataset
                    results_ds.dims[len(qloop_group) + len(mloop_group)].label = "I/Q"

    def __enter__(self):
        """Open the HDF5 file and create the structure for streaming."""
        self._create_results_file()
        self._file = h5py.File(self.path, mode="a")

        # Prepare access to each results dataset for easy streaming
        for qprogram_name, qprogram_data in self.structure["qprograms"].items():
            for measurement_name, _ in qprogram_data["measurements"].items():
                self.results[(qprogram_name, measurement_name)] = self._file[
                    f"qprograms/{qprogram_name}/measurements/{measurement_name}/results"
                ]

        return self

    def __exit__(self, *args):
        """Exit the context manager and close the HDF5 file."""
        if self._file is not None:
            self._file.close()

    def __setitem__(self, key: tuple, value: float):
        """Set an item in the results dataset.

        Args:
            key (tuple): A tuple of (qprogram_name, measurement_name, *indices).
            value (float): The value to store in the results dataset.
        """
        qprogram_name, measurement_name, *indices = key
        if isinstance(qprogram_name, int):
            qprogram_name = f"QProgram_{qprogram_name}"
        if isinstance(measurement_name, int):
            measurement_name = f"Measurement_{measurement_name}"
        self.results[(qprogram_name, measurement_name)][tuple(indices)] = value

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

    def set_yaml(self, yaml: str):
        """Set the YAML representation of executed experiment."""
        self._file["yaml"] = yaml

    def set_executed_at(self, dt: datetime):
        """Set the timestamp when execution of the experiment started."""
        self._file["executed_at"] = str(dt)

    def set_execution_time(self, time: float):
        """Set the execution time in seconds."""
        self._file["execution_time"] = time
