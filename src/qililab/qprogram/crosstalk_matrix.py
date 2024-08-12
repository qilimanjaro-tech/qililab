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

from typing import Collection

import numpy as np

from qililab.yaml import yaml


@yaml.register_class
class CrosstalkMatrix:
    """A class to represent a crosstalk matrix where each index corresponds to a bus."""

    def __init__(self):
        """Initializes an empty crosstalk matrix."""
        self.matrix: dict[str, dict[str, float]] = {}

    def to_array(self) -> np.ndarray:
        """Returns the np.array representation of the crosstalk matrix.

        Returns:
            np.ndarray: crosstalk matrix as a numpy array.
        """
        xtalk_matrix = np.empty(shape=[len(self.matrix), len(self.matrix)])
        for i, bus1 in enumerate(self.matrix):
            for j, bus2 in enumerate(self.matrix[bus1]):
                xtalk_matrix[i, j] = self.matrix[bus1][bus2]
        return xtalk_matrix

    def inverse(self) -> dict[str, dict[str, float]]:
        """Returns the inverse version of the crosstalk matrix (as a bus dictionary).

        Returns:
            dict[str, dict[str, float]]: inverse crosstalk matrix
        """

        inverse_xtalk_array = np.linalg.inv(self.to_array())
        inverse_xtalk_matrix = self.matrix.copy()
        for i, bus1 in enumerate(self.matrix):
            for j, bus2 in enumerate(self.matrix[bus1]):
                inverse_xtalk_matrix[bus1][bus2] = inverse_xtalk_array[i, j]
        return inverse_xtalk_matrix

    def __matmul__(self, flux: dict[str, float]) -> dict[str, float]:
        """Matrix multiplication for flux correction. Corrects a flux vector using the inverse crosstalk matrix

        Args:
            flux (dict[str,float]): Flux vector to correct

        Returns:
            dict[str,float]: Corrected flux vector
        """
        # TODO: test that we're not mixing up rows and columns
        inverse_matrix = self.inverse()
        return {
            xtalk_bus1: sum(
                inverse_matrix[xtalk_bus1][xtalk_bus2] * flux[xtalk_bus2] for xtalk_bus2 in inverse_matrix[xtalk_bus1]
            )
            for xtalk_bus1 in flux
        }

    def __getitem__(self, bus: str) -> dict[str, float]:
        """Returns the dictionary of crosstalk values for the given bus.

        Args:
            bus (str): The bus for which to get the crosstalk values.

        Returns:
            dict[str, float]: A dictionary of crosstalk values for the given bus.
        """
        if bus not in self.matrix:
            self.matrix[bus] = {}
        return self.matrix[bus]

    def __setitem__(self, key: str, value: dict[str, float]) -> None:
        """Sets the crosstalk values for the given bus.

        Args:
            key (str): The bus for which to set the crosstalk values.
            value (dict[str, float]): A dictionary of crosstalk values to set for the given bus.
        """
        self.matrix[key] = value

    def __repr__(self) -> str:
        """Returns a string representation of the CrosstalkMatrix.

        Returns:
            str: A string representation of the CrosstalkMatrix.
        """
        return f"CrosstalkMatrix({self.matrix})"

    def __str__(self) -> str:
        """Produces a string representation of the matrix with rows and columns, labels included.
        The diagonal contains "\", since there is no value there, and if a value doesn't exist, the default 1.0 is shown.

        Returns:
            str: A string representation of the crosstalk matrix.
        """
        buses: set[str] = set(self.matrix.keys())
        for values in self.matrix.values():
            buses.update(values.keys())

        sorted_buses = sorted(buses)
        col_width = max(len(bus) for bus in sorted_buses) + 4  # Determine column width
        header = " " * col_width + " ".join(f"{bus:>{col_width}}" for bus in sorted_buses) + "\n"
        rows = []
        for bus1 in sorted_buses:
            row = [f"{bus1:{col_width}}"]
            for bus2 in sorted_buses:
                if bus1 == bus2:
                    row.append("\\".rjust(col_width))
                else:
                    row.append(f"{self.matrix.get(bus1, {}).get(bus2, 1.0):{col_width}.1f}")
            rows.append(" ".join(row))
        return header + "\n".join(rows)

    @classmethod
    def from_buses(cls, buses: Collection[str]) -> "CrosstalkMatrix":
        """
        Creates a CrosstalkMatrix with all possible associations set to 1.0.

        Args:
            buses (Sequence[str]): A sequence of bus names.

        Returns:
            CrosstalkMatrix: An instance of CrosstalkMatrix with all associations set to 1.0.
        """
        instance = cls()
        instance.matrix = {bus1: {bus2: 1.0 for bus2 in buses if bus1 != bus2} for bus1 in buses}
        return instance
