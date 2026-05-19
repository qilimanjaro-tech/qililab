# Copyright 2026 Qilimanjaro Quantum Tech
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

from __future__ import annotations

from typing import Mapping

import numpy as np
from scipy.special import jv

from qililab.yaml import yaml


@yaml.register_class
class CrosstalkMatrix:
    """A class to represent a crosstalk matrix where each index corresponds to a bus."""

    def __init__(self) -> None:
        """Initializes an empty crosstalk matrix."""
        self.matrix: dict[str, dict[str, float]] = {}
        self.flux_offsets: dict[str, float] = {}
        self.resistances: dict[str, float | None] = {}

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

        if key not in self.resistances:
            self.resistances[key] = None

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
            if self.matrix and bus not in self.matrix:
                raise ValueError(f"Bus {bus} not included inside matrix.")
            self.flux_offsets[bus] = offset[bus]

    def set_resistances(self, resistances: dict[str, float]):
        """Modifies the resistances dictionary based on the given bus and resistance value.

        Args:
            resistances (dict[str, float]): dictionary containing the resistances for each bus to be added or modified and the value of said resistance
        """
        for bus in resistances:
            self.resistances[bus] = resistances[bus]

    def flux_to_bias(self, flux: Mapping[str, float | np.ndarray]) -> dict[str, float | np.ndarray]:
        """Converts target flux values to hardware bias values using linear inversion.

        Applies the inverse of the crosstalk matrix to the flux vector, accounting for
        flux offsets. Both scalar and array inputs are supported — array inputs are
        processed element-wise, enabling sweep-based use cases.

        Args:
            flux (dict[str, float | np.ndarray]): Target flux values keyed by bus name.
                Values can be scalars or numpy arrays of the same length.

        Returns:
            dict[str, float | np.ndarray]: Hardware bias values keyed by bus name.
        """
        sorted_buses = sorted(self.matrix.keys())
        inverse = self.inverse()
        inverse.flux_offsets = self.flux_offsets

        bias = {}
        for bus_1 in sorted_buses:
            bias[bus_1] = sum(
                (flux[bus_2] - inverse.flux_offsets[bus_2]) * inverse.matrix[bus_1][bus_2]
                for bus_2 in inverse.matrix[bus_1].keys()
            )  # type: ignore[assignment]
        return bias

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

        if not instance.resistances:
            for bus in buses:
                instance.resistances[bus] = None
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

        if not instance.resistances:
            for bus in buses:
                instance.resistances[bus] = None
        return instance


@yaml.register_class
class NonLinearCrosstalkMatrix(CrosstalkMatrix):
    """Extends CrosstalkMatrix with nonlinear crosstalk correction terms.

    The nonlinear correction models the flux induced on qubit i by coupler j
    as a Bessel-series expansion:

        delta_phi_i = 2 * amp_ij * sum_{k=1}^{K} [J_k(k*beta_ij) / (k*beta_ij)] * sin(k * 2pi * phi_j)

    where beta_ij and amp_ij are stored in ``beta_c_matrix`` and ``non_lin_amp_matrix``
    respectively. Entries that are None indicate no nonlinear coupling between that pair.
    """

    def __init__(self) -> None:
        """Initializes an empty nonlinear crosstalk matrix."""
        super().__init__()
        self.beta_c_matrix: dict[str, dict[str, float | None]] = {}
        self.non_lin_amp_matrix: dict[str, dict[str, float | None]] = {}
        self.junction_asym_matrix: dict[str, dict[str, float | None]] = {}

    def __setitem__(self, key: str, value: dict[str, float]) -> None:
        """Sets the crosstalk values for the given bus and initializes nonlinear entries.

        Args:
            key (str): The bus for which to set the crosstalk values.
            value (dict[str, float]): A dictionary of crosstalk values.
        """
        super().__setitem__(key, value)

        if key not in self.beta_c_matrix:
            self.beta_c_matrix[key] = dict.fromkeys(value)
        else:
            for bus in value:
                if bus not in self.beta_c_matrix[key]:
                    self.beta_c_matrix[key][bus] = None

        if key not in self.non_lin_amp_matrix:
            self.non_lin_amp_matrix[key] = dict.fromkeys(value)
        else:
            for bus in value:
                if bus not in self.non_lin_amp_matrix[key]:
                    self.non_lin_amp_matrix[key][bus] = None
        if key not in self.junction_asym_matrix:
            self.junction_asym_matrix[key] = dict.fromkeys(value)
        else:
            for bus in value:
                if bus not in self.junction_asym_matrix[key]:
                    self.junction_asym_matrix[key][bus] = None

    def set_non_linear_params(
        self,
        bus_i: str,
        bus_j: str,
        beta_c: float | None = None,
        amplitude: float | None = None,
        junction_asym: float | None = None,
    ) -> None:
        """Sets the nonlinear coupling parameters between bus_i (target) and bus_j (source).

        Args:
            bus_i (str): The bus that receives the nonlinear flux correction.
            bus_j (str): The bus whose flux drives the nonlinear term.
            beta_c (float): Bessel modulation parameter beta_c. Must be non-zero.
            amplitude (float): Amplitude of the nonlinear correction in flux units.
            junction_asym (float): Junction asymmetry, d ∈ [-1, 1].

        Raises:
            ValueError: If either bus is not present in the matrix.
            ValueError: If beta_c is zero, which would cause a division by zero in the
                Bessel expansion.
        """
        for bus in (bus_i, bus_j):
            if bus not in self.matrix:
                raise ValueError(f"Bus '{bus}' not present in the crosstalk matrix.")

        if beta_c is not None or amplitude is not None:
            if not (beta_c is not None and amplitude is not None):
                raise ValueError(
                    "Both 'amplitude' and 'beta_c' must be provided together — you cannot specify one without the other."
                )

            if beta_c == 0:
                raise ValueError("beta_c cannot be zero: it appears as a divisor in the Bessel expansion ")

            if bus_i not in self.beta_c_matrix:
                self.beta_c_matrix[bus_i] = {}
            if bus_i not in self.non_lin_amp_matrix:
                self.non_lin_amp_matrix[bus_i] = {}

            self.beta_c_matrix[bus_i][bus_j] = beta_c
            self.non_lin_amp_matrix[bus_i][bus_j] = amplitude

        if junction_asym is not None:
            if bus_i not in self.junction_asym_matrix:
                self.junction_asym_matrix[bus_i] = {}
            self.junction_asym_matrix[bus_i][bus_j] = junction_asym

    def sin_beta_scaled(
        self,
        flux: float | np.ndarray,
        beta: float,
        amp: float,
        k_max: int = 50,
    ) -> np.ndarray:
        """Evaluates the Bessel-series nonlinear flux term.

        Args:
            flux (float | np.ndarray): Flux value(s) in units of phi_0.
            beta (float): Bessel modulation parameter.
            amp (float): Amplitude scaling factor.
            k_max (int): Number of terms in the Bessel expansion. Defaults to 50.

        Returns:
            np.ndarray: Nonlinear flux correction.

        Raises:
            ValueError: If amp is NaN.
        """
        if np.isnan(amp):
            raise ValueError("Amplitude cannot be NaN. Set non_lin_amp_matrix accordingly.")

        phi = np.asarray(flux, dtype=float) * 2 * np.pi
        result = np.zeros_like(phi, dtype=float)
        for k in range(1, k_max + 1):
            result += (jv(k, k * beta) / (k * beta)) * np.sin(k * phi)
        return 2 * result * amp

    def junction_asymmetry_correction(self, flux_x: float | np.ndarray, d: float) -> float | np.ndarray:
        """Effective flux shift from SQUID junction asymmetry in a fluxonium.

        For a SQUID loop with asymmetry d = (E_J2 - E_J1)/(E_J1 + E_J2), the
        external flux Φ_x induces an additional phase
            φ_d = arctan(d · tan(π Φ_x / Φ_0)),
        equivalent to a flux offset Δφ = -φ_d / (2π) (in units of Φ_0) that
        must be subtracted from the target flux before inverting the linear
        crosstalk. Vanishes for a symmetric SQUID (d = 0).

        Args:
            flux_x (float | np.ndarray): Applied flux through the SQUID loop, in units of Φ_0.
            d (float): Junction asymmetry, d ∈ [-1, 1].

        Raises:
            ValueError: If d is NaN

        Returns:
            float | np.ndarray: Effective flux correction Δφ in units of Φ_0.
        """

        if np.isnan(d):
            raise ValueError("Junction asymetry cannot be NaN. Set junction_asym_matrix accordingly.")
        phi_d = np.arctan(d * np.tan(np.pi * flux_x))
        return -phi_d / (2 * np.pi)

    def get_non_linear_flux_terms(
        self,
        flux: Mapping[str, float | np.ndarray],
    ) -> dict[str, float | np.ndarray]:
        """Computes the nonlinear flux correction for each bus.

        Args:
            flux (Mapping[str, float]): Flux values keyed by bus name.

        Returns:
            dict[str, float]: Nonlinear correction terms keyed by bus name.

        Raises:
            ValueError: If a bus with nonlinear params set is not found in the provided flux dict.
        """
        corrections: dict[str, float | np.ndarray] = dict.fromkeys(flux, 0.0)

        for bus_i, row in self.beta_c_matrix.items():
            for bus_j, beta in row.items():
                if beta is None:
                    continue
                if bus_i not in flux:
                    raise ValueError(
                        f"Bus '{bus_i}' has nonlinear parameters set but was not found "
                        f"in the provided flux dict. All buses with nonlinear corrections "
                        f"must be included."
                    )
                amp = self.non_lin_amp_matrix.get(bus_i, {}).get(bus_j)
                if amp is None:
                    raise ValueError(f"beta_c is set for ({bus_i}, {bus_j}) but non_lin_amp is None.")
                if bus_j not in flux:
                    raise ValueError(f"Bus '{bus_j}' not found in provided flux dict.")
                result = self.sin_beta_scaled(flux=flux[bus_j], beta=beta, amp=amp)
                corrections[bus_i] += result  # type: ignore[assignment]
        for bus_i in self.junction_asym_matrix:
            for bus_j in self.junction_asym_matrix[bus_i]:
                d = self.junction_asym_matrix[bus_i][bus_j]
                if d is None:
                    continue
                corrections[bus_i] += self.junction_asymmetry_correction(flux_x=flux[bus_j], d=d)

        return corrections

    def flux_to_bias(self, flux: Mapping[str, float | np.ndarray]) -> dict[str, float | np.ndarray]:
        """Converts target flux values to hardware bias values, including nonlinear corrections.

        First computes the nonlinear flux corrections via the Bessel-series expansion and
        adds them to the target flux values, then applies the linear matrix inversion to
        obtain the final hardware bias values. Both scalar and array inputs are supported.

        Args:
            flux (Mapping[str, float | np.ndarray]): Target flux values keyed by bus name.
                Values can be scalars or numpy arrays of the same length.

        Returns:
            dict[str, float | np.ndarray]: Hardware bias values keyed by bus name,
                including nonlinear corrections.
        """
        sorted_buses = sorted(self.matrix.keys())

        corrections = self.get_non_linear_flux_terms(flux)
        if all(isinstance(f, (float, int)) for f in flux.values()):
            corrected_flux = np.array([flux[bus] + corrections[bus] for bus in sorted_buses], dtype=float)
        else:
            len_wf = max(len(flux[bus]) for bus in sorted_buses if not isinstance(flux[bus], (float, int)))  # type: ignore[arg-type]
            corrected_flux = np.array(
                [
                    flux[bus]
                    + (
                        corrections[bus]
                        if isinstance(corrections[bus], np.ndarray)
                        else np.array([corrections[bus]] * len_wf)
                    )
                    for bus in sorted_buses
                ],
                dtype=float,
            )
        offsets = np.array([self.flux_offsets.get(bus, 0.0) for bus in sorted_buses])

        inverse_matrix = self.inverse().to_array()
        corr_m_off = corrected_flux.T - offsets
        bias_array = inverse_matrix @ corr_m_off.T

        return dict(zip(sorted_buses, bias_array))

    @classmethod
    def from_linear(cls, linear: CrosstalkMatrix) -> "NonLinearCrosstalkMatrix":
        """Creates a NonLinearCrosstalkMatrix from an existing linear CrosstalkMatrix,
        copying all its data and initializing nonlinear parameters to None.

        Args:
            linear (CrosstalkMatrix): An existing linear crosstalk matrix.

        Returns:
            NonLinearCrosstalkMatrix: A new instance with linear parameters copied.
        """
        instance = cls()
        instance.matrix = {bus: dict(row) for bus, row in linear.matrix.items()}
        instance.flux_offsets = dict(linear.flux_offsets)
        instance.resistances = dict(linear.resistances)
        instance.beta_c_matrix = {bus: dict.fromkeys(row) for bus, row in linear.matrix.items()}
        instance.non_lin_amp_matrix = {bus: dict.fromkeys(row) for bus, row in linear.matrix.items()}
        instance.junction_asym_matrix = {bus: dict.fromkeys(row) for bus, row in linear.matrix.items()}
        return instance

    def __repr__(self) -> str:
        return f"NonLinearCrosstalkMatrix({self.matrix}, beta_c={self.beta_c_matrix})"
