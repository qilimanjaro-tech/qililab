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

from copy import deepcopy
import numpy as np

from qililab.yaml import yaml


@yaml.register_class
class CrosstalkMatrix:
    """A class to represent a crosstalk matrix where each index corresponds to a bus."""

    def __init__(self) -> None:
        """Initializes an empty crosstalk matrix."""
        self.matrix: dict[str, dict[str, float]] = {}
        self.flux_offsets: dict[str, float] = {}

    def to_array(self) -> np.ndarray:
        """Returns the np.array representation of the crosstalk matrix.

        Returns:
            np.ndarray: crosstalk matrix as a numpy array.
        """
        buses: set[str] = set(self.matrix.keys())
        for values in self.matrix.values():
            buses.update(values.keys())

        sorted_buses = sorted(buses)

        xtalk_matrix = np.empty(shape=[len(self.matrix), len(self.matrix)])
        for i, bus1 in enumerate(sorted_buses):
            for j, bus2 in enumerate(sorted_buses):
                xtalk_matrix[i, j] = self.matrix[bus1][bus2]
        return xtalk_matrix

    def inverse(self) -> "CrosstalkMatrix":
        """Returns the inverse version of the crosstalk matrix (as a bus dictionary).

        Returns:
            CrosstalkMatrix: inverse crosstalk matrix
        """
        inverse_xtalk_array = np.linalg.inv(self.to_array())
        return self.from_array(list(self.matrix.keys()), inverse_xtalk_array)

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
        if key not in self.matrix:
            self.matrix[key] = value
        else:
            for bus in value.keys():
                self.matrix[key][bus] = value[bus]

        if key not in self.flux_offsets:
            self.flux_offsets[key] = 0.0

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
                row.append(f"{self.matrix.get(bus1, {}).get(bus2, 1.0):{col_width}}")
            rows.append(" ".join(row))
        return header + "\n".join(rows)

    def set_offset(self, offset: dict[str, float]):
        """Modifies the offset based on the given bus and offset value

        Args:
            offset (dict[str, float]): dictionary containing the buses of the offsets to be added or modified and the value of said offsets
        """
        for bus in offset:
            self.flux_offsets[bus] = offset[bus]

    @classmethod
    def from_array(cls, buses: list[str], matrix_array: np.ndarray) -> "CrosstalkMatrix":
        """Creates crosstalk matrix from an array and corresponding set of buses. For a set of buses
        [bus1,bus2,...,busN] the corresponding matrix should have the same indices for rows and columns
        i.e. for the set of buses [bus1,bus2,...,busN], matrix[0,0] will be the coefficient for bus1[bus1],
        matrix[0,1] will be bus1[bus2], etc.

        Args:
            buses (list[str]): ordered list of buses for the crosstalk matrix
            matrix_array (np.ndarray): crosstalk matrix numpy array

        Returns:
            CrosstalkMatrix: CrosstalkMatrix: An instance of CrosstalkMatrix
        """

        instance = cls()
        instance.matrix = {}
        for i, bus1 in enumerate(buses):
            for j, bus2 in enumerate(buses):
                if bus1 not in instance.matrix:
                    instance.matrix[bus1] = {}
                instance.matrix[bus1][bus2] = float(matrix_array[i, j])

        if not instance.flux_offsets:
            for bus in buses:
                instance.flux_offsets[bus] = 0.0
        return instance

    @classmethod
    def from_buses(cls, buses: dict[str, dict[str, float]]) -> "CrosstalkMatrix":
        """
        Creates a CrosstalkMatrix with all possible associations set to 1.0.

        Args:
            buses (Sequence[str]): A sequence of bus names.

        Returns:
            CrosstalkMatrix: An instance of CrosstalkMatrix with all associations set to 1.0.
        """
        instance = cls()
        instance.matrix = {}
        instance.matrix = {bus1: {bus2: buses[bus1][bus2] for bus2 in buses} for bus1 in buses}

        if not instance.flux_offsets:
            for bus in buses:
                instance.flux_offsets[bus] = 0.0
        return instance


@yaml.register_class
class FluxVector:
    """Class to represent a flux vector. This is a dictionary of bus[flux] values"""

    def __init__(self) -> None:
        self.flux_vector: dict[str, float | list[float] | np.ndarray] = {}
        self.bias_vector: dict[str, float | list[float] | np.ndarray] = {}
        self.crosstalk: CrosstalkMatrix | None = None
        self.crosstalk_inverse: CrosstalkMatrix | None = None

    def __getitem__(self, bus: str) -> float | list[float] | np.ndarray:
        """Given a bus, returns its corresponding flux

        Args:
            bus (str): The bus for which to get the flux values.

        Returns:
            float: Flux value for the given bus
        """
        if self.bias_vector:
            return self.bias_vector[bus]
        return self.flux_vector[bus]

    def __setitem__(self, key: str, flux: float | list[float] | np.ndarray) -> None:
        """Given a bus, sets a new flux

        Args:
            key (str): The bus for which to set the flux values.
            flux (float): The new value for the given flux.

        """

        self.flux_vector[key] = flux
        if self.crosstalk:
            self.set_crosstalk(self.crosstalk)

    def set_crosstalk(self, crosstalk: CrosstalkMatrix):
        """Set the crosstalk compensation on the existing flux vector. This function does the matrix product to calculate the correct flux

        Args:
            crosstalk (CrosstalkMatrix): _description_
        """
        self.crosstalk = crosstalk
        self.crosstalk_inverse = crosstalk.inverse()
        self.crosstalk_inverse.flux_offsets = self.crosstalk.flux_offsets

        for bus in self.crosstalk_inverse.matrix.keys():
            if bus not in self.flux_vector:
                self.flux_vector[bus] = 0

            if isinstance(self.flux_vector[bus], list):
                self.flux_vector[bus] = np.array(self.flux_vector[bus])

        self.bias_vector = self.flux_vector.copy()

        for bus_1 in self.crosstalk_inverse.matrix.keys():
            self.bias_vector[bus_1] = sum(
                (self.flux_vector[bus_2] - self.crosstalk_inverse.flux_offsets[bus_2])  # type: ignore
                * self.crosstalk_inverse.matrix[bus_1][bus_2]
                for bus_2 in self.crosstalk_inverse.matrix[bus_1].keys()
            )

        return self.bias_vector

    def set_crosstalk_from_bias(
        self, crosstalk: CrosstalkMatrix, bias_vector: dict[str, float | list[float] | np.ndarray] | None = None
    ):
        """Set the crosstalk compensation on the existing flux vector. This function does the matrix product to calculate the correct flux

        Args:
            crosstalk (CrosstalkMatrix): _description_

        """
        self.crosstalk = crosstalk

        if bias_vector:
            self.bias_vector = bias_vector.copy()
        if not self.bias_vector:
            self.bias_vector = self.flux_vector.copy()

        # Add duration logic!!!!!
        for bus_1 in self.crosstalk.matrix.keys():
            self.flux_vector[bus_1] = (
                sum(
                    (self.bias_vector[bus_2] * self.crosstalk.matrix[bus_1][bus_2])  # type: ignore
                    for bus_2 in self.crosstalk.matrix[bus_1].keys()
                )
                + self.crosstalk.flux_offsets[bus_1]
            )

        return self.flux_vector

    def to_dict(self):
        """To dictionary method, returns the vector's dictionary

        Returns:
            dict[str, float]: Flux vector dictionary
        """
        if self.bias_vector:
            return self.bias_vector
        return self.flux_vector

    def get_decomposed_vector(self, bus_list: list[str] | None = None):
        """Return dictionary with flux vector decomposed by variables, for each flux return a flux vector considering
        the rest of fluxes (or the rest of the fluxes from the bus_list if given) as 0.
        This is typically used to sum variables in flux vs flux Qprogram.

        Args:
            flux_dict (optional, list[str] | None): List of fluxes to be decomposed. Defaults to None

        Returns:
            dict[str, float]: Dictionary containing different flux vectors for each bus.
        """
        list_fluxes = {}
        if self.crosstalk:
            for bus in self.crosstalk.matrix.keys():
                flux_vector_copy = deepcopy(self)
                for zero_flux in self.crosstalk.matrix.keys():
                    if bus_list is not None and bus in bus_list and zero_flux in bus_list and zero_flux != bus:
                        flux_vector_copy[zero_flux] = 0
                    elif bus_list is None and zero_flux != bus:
                        flux_vector_copy[zero_flux] = 0
                if (bus_list is not None and bus in bus_list) or bus_list is None:
                    list_fluxes[bus] = flux_vector_copy
        return list_fluxes

    @classmethod
    def from_dict(cls, flux_dict: dict[str, float | list[float] | np.ndarray]) -> "FluxVector":
        """Creates a FluxVector instance from a dictionary of bus[flux]

        Args:
            flux_dict (dict[str,float]): Dictionary containing buses as keys and fluxes as values

        Returns:
            FluxVector: FluxVector instance
        """
        instance = cls()
        instance.flux_vector = flux_dict
        return instance
