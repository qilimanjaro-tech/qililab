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

import warnings
from dataclasses import dataclass
from typing import Final, Mapping, cast

import numpy as np
import xarray as xr
from scipy.special import jv

from qililab.utils import Sentinel, Unset, sort_buses
from qililab.yaml import yaml

_UNSET: Final = Sentinel.UNSET

# Magnetic flux quantum, Φ₀ = h / (2e), in webers.
PHI_0_WB: Final = 2.067833848e-15

_BUS_OUT: Final = "bus_out"
_BUS_IN: Final = "bus_in"


def _rescale_by_resistance(
    matrix: dict[str, dict[str, float]], flux_line_resistances_ohms: dict[str, float], *, invert: bool
) -> dict[str, dict[str, float]]:
    missing = sort_buses(
        {col for cols in matrix.values() for col in cols if flux_line_resistances_ohms.get(col) is None}
    )
    if missing:
        raise ValueError(f"Missing resistance for flux line(s): {missing}")
    converted_matrix: dict[str, dict[str, float]] = {}
    for bus_1, dict_buses in matrix.items():
        converted_matrix[bus_1] = {}
        for bus_2, value in dict_buses.items():
            factor = PHI_0_WB * flux_line_resistances_ohms[bus_2] * 1e12
            converted_matrix[bus_1][bus_2] = value / factor if invert else value * factor
    return converted_matrix


def convert_phi0_per_volt_to_pH(
    matrix: dict[str, dict[str, float]], flux_line_resistances_ohms: dict[str, float]
) -> dict[str, dict[str, float]]:
    """Convert a crosstalk matrix from units of Φ₀/V to pH, using the provided line resistances.

    Args:
        matrix (dict): Crosstalk matrix dict ``{row_label: {col_label: value_in_phi0_per_volt}}``.
        flux_line_resistances_ohms (dict): Line resistances in ohms ``{line_label: resistance}``.

    Returns:
        dict: Nested dict with the same structure as ``matrix``, values converted to pH.

    Raises:
        ValueError: If a drive line involved lacks a resistance.
    """
    return _rescale_by_resistance(matrix, flux_line_resistances_ohms, invert=False)


def convert_pH_to_phi0_per_volt(
    matrix: dict[str, dict[str, float]], flux_line_resistances_ohms: dict[str, float]
) -> dict[str, dict[str, float]]:
    """Convert a crosstalk matrix from units of pH to Φ₀/V, using the provided line resistances.

    Args:
        matrix (dict): Crosstalk matrix dict ``{row_label: {col_label: value_in_pH}}``.
        flux_line_resistances_ohms (dict): Line resistances in ohms ``{line_label: resistance}``.

    Returns:
        dict: Nested dict with the same structure as ``matrix``, values converted to Φ₀/V.

    Raises:
        ValueError: If a drive line involved lacks a resistance.
    """
    return _rescale_by_resistance(matrix, flux_line_resistances_ohms, invert=True)


@dataclass
class _CrosstalkCache:
    """Numeric view of a :class:`CrosstalkMatrix`."""

    buses: list[str]
    # matrix has these dimensions (bus_out, bus_in), coords = buses
    matrix: xr.DataArray
    inverse: xr.DataArray
    version: int
    source: dict[str, dict[str, float]]


class _RowView(dict):
    """Transient, write-through view of a single crosstalk-matrix row."""

    def __init__(self, parent: "CrosstalkMatrix", bus: str) -> None:
        self._parent = parent
        self._bus = bus
        existed = bus in parent.matrix
        row = parent.matrix.setdefault(bus, {})
        super().__init__(row)
        if not existed:
            # Adding a new (empty) row changes the set of buses seen by to_array().
            parent._invalidate()

    def __setitem__(self, key: str, value: float) -> None:
        super().__setitem__(key, value)
        self._parent.matrix[self._bus][key] = value
        self._parent._invalidate()

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key)
        self._parent.matrix[self._bus].pop(key, None)
        self._parent._invalidate()

    def update(self, *args, **kwargs) -> None:  # type: ignore[override]
        super().update(*args, **kwargs)
        self._parent.matrix[self._bus].update(dict(*args, **kwargs))
        self._parent._invalidate()


@yaml.register_class
class CrosstalkMatrix:
    """A class to represent a crosstalk matrix where each index corresponds to a bus."""

    _cache: "_CrosstalkCache | None" = None
    _version: int = 0

    def __init__(self) -> None:
        """Initializes an empty crosstalk matrix."""
        self.matrix: dict[str, dict[str, float]] = {}
        self.flux_offsets: dict[str, float] = {}
        self.resistances: dict[str, float | None] = {}
        self._cache = None
        self._version = 0

    def _invalidate(self) -> None:
        """Marks the cached array stale after an in-place mutation of ``matrix``."""
        self._version += 1

    def __getstate__(self) -> dict:
        """Serialized state: only the persistent dicts, never the derived array cache."""
        state = self.__dict__.copy()
        state.pop("_cache", None)
        state.pop("_version", None)
        return state

    def _get_cache(self) -> "_CrosstalkCache":
        """Returns the memoized labeled array/inverse, rebuilding only when ``matrix`` changed."""
        cache = self._cache
        if cache is not None and cache.source is self.matrix and cache.version == self._version:
            return cache

        buses = self._sorted_buses()
        n = len(buses)
        index = {bus: i for i, bus in enumerate(buses)}
        data = np.eye(n)
        for bus1, row in self.matrix.items():
            if row:
                data[index[bus1], [index[bus2] for bus2 in row]] = list(row.values())

        coords = {_BUS_OUT: buses, _BUS_IN: buses}
        matrix_da = xr.DataArray(data, dims=(_BUS_OUT, _BUS_IN), coords=coords)
        inverse_data = np.linalg.inv(data) if n else np.zeros((0, 0))
        inverse_da = xr.DataArray(inverse_data, dims=(_BUS_OUT, _BUS_IN), coords=coords)

        self._cache = _CrosstalkCache(buses, matrix_da, inverse_da, self._version, self.matrix)
        return self._cache

    def _sorted_buses(self) -> list[str]:
        """Canonical bus ordering shared by to_array/inverse/from_array.

        Every method that turns the matrix into an array (or back) must agree on the
        row/column order, otherwise the array and its bus labels drift apart and the
        inverse — and every bias derived from it — is silently mislabeled. Includes
        every bus that appears as a row or as a column of the matrix.

        Returns:
            list[str]: The matrix's buses in canonical (see :func:`sort_buses`) order.
        """
        buses: set[str] = set(self.matrix.keys())
        for values in self.matrix.values():
            buses.update(values.keys())
        return sort_buses(buses)

    def to_array(self) -> np.ndarray:
        """Returns the np.array representation of the crosstalk matrix.

        Returns:
            np.ndarray: crosstalk matrix as a numpy array.
        """
        return self._get_cache().matrix.values.copy()

    def inverse(self) -> "CrosstalkMatrix":
        """Returns the inverse version of the crosstalk matrix (as a bus dictionary).

        Returns:
            CrosstalkMatrix: inverse crosstalk matrix
        """
        cache = self._get_cache()
        return self.from_array(cache.buses, cache.inverse.values)

    def __getitem__(self, bus: str) -> dict[str, float]:
        """Returns the dictionary of crosstalk values for the given bus.

        Args:
            bus (str): The bus for which to get the crosstalk values.

        Returns:
            dict[str, float]: A dictionary of crosstalk values for the given bus.
        """
        return _RowView(self, bus)

    def __setitem__(self, key: str, value: dict[str, float]) -> None:
        """Sets the crosstalk values for the given bus.

        Args:
            key (str): The bus for which to set the crosstalk values.
            value (dict[str, float]): A dictionary of crosstalk values to set for the given bus.
        """
        if key not in self.matrix:
            self.matrix[key] = dict(value)
        else:
            for bus in value.keys():
                self.matrix[key][bus] = value[bus]

        if key not in self.flux_offsets:
            self.flux_offsets[key] = 0.0

        if key not in self.resistances:
            self.resistances[key] = None

        self._invalidate()

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
        sorted_buses = self._sorted_buses()
        # Determine column width
        col_width = max(len(bus) for bus in sorted_buses) + 4
        header = " " * col_width + " ".join(f"{bus:>{col_width}}" for bus in sorted_buses) + "\n"
        rows = []
        for bus1 in sorted_buses:
            row = [f"{bus1:{col_width}}"]
            for bus2 in sorted_buses:
                row.append(f"{self.matrix.get(bus1, {}).get(bus2, 0.0):{col_width}}")
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
        missing = tuple(bus for bus in self._sorted_buses() if self.resistances.get(bus) is None)
        if missing:
            warnings.warn(
                f"Missing resistances for flux lines: {missing}. Add them with set_resistances(), "
                "or CrosstalkMatrix will fail upon any operation."
            )

    def in_phi0_per_volt(self) -> "CrosstalkMatrix":
        """Return an equivalent crosstalk matrix with values expressed in Φ₀/V.
        The matrix is stored in pH (mutual inductance, resistance-independent), but the
        linear inversion that turns target fluxes into hardware bias *voltages* operates
        in Φ₀/V (the slope of flux vs. applied voltage).

        Returns:
            CrosstalkMatrix: Equivalent matrix expressed in Φ₀/V.

        Raises:
            ValueError: If any drive line involved lacks a resistance.
        """
        instance = CrosstalkMatrix()
        instance.matrix = convert_pH_to_phi0_per_volt(self.matrix, cast("dict[str, float]", self.resistances))
        instance.flux_offsets = dict(self.flux_offsets)
        instance.resistances = dict(self.resistances)
        return instance

    def flux_to_bias(self, flux: Mapping[str, float | np.ndarray]) -> dict[str, float | np.ndarray]:
        """Converts target flux values to hardware bias values using linear inversion.

        The matrix is stored in pH, so it is first converted to Φ₀/V using the per-line
        resistances (see :meth:`in_phi0_per_volt`) and the inverse of that is applied to the
        flux vector, accounting for flux offsets. Both scalar and array inputs are supported,
        array inputs are processed element-wise, enabling sweep-based use cases.

        Args:
            flux (dict[str, float | np.ndarray]): Target flux values keyed by bus name.
                Values can be scalars or numpy arrays of the same length.

        Returns:
            dict[str, float | np.ndarray]: Hardware bias values keyed by bus name.

        Raises:
            ValueError: If any drive line involved lacks a resistance.
        """
        cache = self._get_cache()
        buses = cache.buses

        missing = sort_buses({bus for bus in buses if self.resistances.get(bus) is None})
        if missing:
            raise ValueError(f"Missing resistance for flux line(s): {missing}")
        # The matrix is stored in pH; the bias inversion runs in Φ₀/V. The Φ₀/V matrix is the pH
        # matrix column-scaled by 1/(Φ₀·R·1e12), so its inverse is the (memoized) pH inverse
        # row-scaled by (Φ₀·R·1e12) — reuse the cached inverse instead of re-inverting per call.
        factors = np.array([PHI_0_WB * self.resistances[bus] * 1e12 for bus in buses])
        inverse = cache.inverse.values * factors[:, np.newaxis]

        offsets = np.array([self.flux_offsets.get(bus, 0.0) for bus in buses])
        flux_values = [flux[bus] for bus in buses]
        scalar_input = all(isinstance(value, (int, float, np.number)) for value in flux_values)

        if scalar_input:
            bias = inverse @ (np.array(flux_values, dtype=float) - offsets)
            return {bus: float(value) for bus, value in zip(buses, bias)}

        length = max(np.asarray(value).size for value in flux_values)
        flux_stack = np.stack([np.broadcast_to(np.asarray(value, dtype=float), length) for value in flux_values])
        bias = inverse @ (flux_stack - offsets[:, np.newaxis])
        return dict(zip(buses, bias))

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
        rows = np.asarray(matrix_array, dtype=float).tolist()
        instance.matrix = {bus1: dict(zip(buses, rows[i])) for i, bus1 in enumerate(buses)}

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


@dataclass
class _NonLinearCache:
    """Sparse index of the non-None nonlinear terms of a :class:`NonLinearCrosstalkMatrix`."""

    version: int
    beta_terms: list[tuple[str, str, float]]
    junction_terms: list[tuple[str, str, float]]


@yaml.register_class
class NonLinearCrosstalkMatrix(CrosstalkMatrix):
    """Extends CrosstalkMatrix with nonlinear crosstalk correction terms.

    The nonlinear correction models the flux induced on qubit i by coupler j
    as a Bessel-series expansion:

        delta_phi_i = 2 * amp_ij * sum_{k=1}^{K} [J_k(k*beta_ij) / (k*beta_ij)] * sin(k * 2pi * phi_j)

    where beta_ij and amp_ij are stored in ``beta_c_matrix`` and ``non_lin_amp_matrix``
    respectively. Entries that are None indicate no nonlinear coupling between that pair.
    """

    _nonlinear_cache: "_NonLinearCache | None" = None
    _nonlinear_version: int = 0

    def __init__(self) -> None:
        """Initializes an empty nonlinear crosstalk matrix."""
        super().__init__()
        self.beta_c_matrix: dict[str, dict[str, float | None]] = {}
        self.non_lin_amp_matrix: dict[str, dict[str, float | None]] = {}
        self.junction_asym_matrix: dict[str, dict[str, float | None]] = {}
        self._nonlinear_cache = None
        self._nonlinear_version = 0

    def __getstate__(self) -> dict:
        """Serialized state drops the derived nonlinear index too (kept dense in the dicts)."""
        state = super().__getstate__()
        state.pop("_nonlinear_cache", None)
        state.pop("_nonlinear_version", None)
        return state

    def _active_nonlinear_terms(self) -> "_NonLinearCache":
        """Returns the non-None nonlinear terms, rebuilding only when they changed."""
        cache = self._nonlinear_cache
        if cache is not None and cache.version == self._nonlinear_version:
            return cache

        beta_terms = [
            (bus_i, bus_j, beta)
            for bus_i, row in self.beta_c_matrix.items()
            for bus_j, beta in row.items()
            if beta is not None
        ]
        junction_terms = [
            (bus_i, bus_j, d)
            for bus_i, row in self.junction_asym_matrix.items()
            for bus_j, d in row.items()
            if d is not None
        ]
        self._nonlinear_cache = _NonLinearCache(self._nonlinear_version, beta_terms, junction_terms)
        return self._nonlinear_cache

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

        self._nonlinear_version += 1

    def set_non_linear_params(
        self,
        bus_i: str,
        bus_j: str,
        beta_c: float | Unset | None = _UNSET,
        amplitude: float | Unset | None = _UNSET,
        junction_asym: float | Unset | None = _UNSET,
    ) -> None:
        """Sets the nonlinear coupling parameters between bus_i (target) and bus_j (source).
            None eliminates the value stored.

        Args:
            bus_i (str): The bus that receives the nonlinear flux correction.
            bus_j (str): The bus whose flux drives the nonlinear term.
            beta_c (float | None): Bessel modulation parameter beta_c. Must be non-zero.
            amplitude (float | None): Amplitude of the nonlinear correction in flux units.
            junction_asym (float | None): Junction asymmetry, d ∈ [-1, 1].

        Raises:
            ValueError: If either bus is not present in the matrix.
            ValueError: If beta_c is zero, which would cause a division by zero in the
                Bessel expansion.
            ValueError: If both "amplitude" and "beta_c" aren't set to the same type of value.
                i.e. amplitude set to a float and beta to none or unset.
        """
        for bus in (bus_i, bus_j):
            if bus not in self.matrix:
                raise ValueError(f"Bus '{bus}' not present in the crosstalk matrix.")

        if beta_c is not _UNSET or amplitude is not _UNSET:
            if beta_c is _UNSET or amplitude is _UNSET:
                raise ValueError(
                    "Both 'amplitude' and 'beta_c' must be provided together — you cannot specify one without the other."
                )
            if (beta_c is None) != (amplitude is None):
                # Errors if you are setting only one of the two parameters to None.
                raise ValueError("You can only set to None 'amplitude' and 'beta_c' together.")

            if beta_c == 0:
                raise ValueError("beta_c cannot be zero: it appears as a divisor in the Bessel expansion ")

            if bus_i not in self.beta_c_matrix:
                self.beta_c_matrix[bus_i] = {}
            if bus_i not in self.non_lin_amp_matrix:
                self.non_lin_amp_matrix[bus_i] = {}

            self.beta_c_matrix[bus_i][bus_j] = beta_c
            self.non_lin_amp_matrix[bus_i][bus_j] = amplitude

        if junction_asym is not _UNSET:
            if bus_i not in self.junction_asym_matrix:
                self.junction_asym_matrix[bus_i] = {}
            self.junction_asym_matrix[bus_i][bus_j] = junction_asym

        self._nonlinear_version += 1

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
        terms = self._active_nonlinear_terms()

        for bus_i, bus_j, beta in terms.beta_terms:
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
        for bus_i, bus_j, d in terms.junction_terms:
            corrections[bus_i] += self.junction_asymmetry_correction(flux_x=flux[bus_j], d=d)

        return corrections

    def flux_to_bias(self, flux: Mapping[str, float | np.ndarray]) -> dict[str, float | np.ndarray]:
        """Converts target flux values to hardware bias values, including nonlinear corrections.

        First computes the nonlinear flux corrections via the Bessel-series expansion and
        adds them to the target flux values, then inverts the linear matrix — converted from
        the stored pH to Φ₀/V with the per-line resistances (see :meth:`in_phi0_per_volt`) — to
        obtain the final hardware bias values. Both scalar and array inputs are supported.

        Args:
            flux (Mapping[str, float | np.ndarray]): Target flux values keyed by bus name.
                Values can be scalars or numpy arrays of the same length.

        Returns:
            dict[str, float | np.ndarray]: Hardware bias values keyed by bus name,
                including nonlinear corrections.

        Raises:
            ValueError: If any drive line involved lacks a resistance.
        """
        cache = self._get_cache()
        sorted_buses = cache.buses

        corrections = self.get_non_linear_flux_terms(flux)
        if all(isinstance(f, (int, float, np.number)) for f in flux.values()):
            corrected_flux = np.array([flux[bus] + corrections[bus] for bus in sorted_buses], dtype=float)
        else:
            len_wf = max(len(flux[bus]) for bus in sorted_buses if not isinstance(flux[bus], (int, float, np.number)))  # type: ignore[arg-type]
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

        missing = sort_buses({bus for bus in sorted_buses if self.resistances.get(bus) is None})
        if missing:
            raise ValueError(f"Missing resistance for flux line(s): {missing}")
        # Inverse of the Φ₀/V matrix = cached pH inverse row-scaled by (Φ₀·R·1e12); see flux_to_bias.
        factors = np.array([PHI_0_WB * self.resistances[bus] * 1e12 for bus in sorted_buses])
        inverse_matrix = cache.inverse.values * factors[:, np.newaxis]
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
