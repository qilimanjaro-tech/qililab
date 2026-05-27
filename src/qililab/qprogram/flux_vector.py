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

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import numpy as np

from qililab.core.variables import Variable, VariableExpression
from qililab.qprogram.blocks import ForLoop, Loop, Parallel
from qililab.qprogram.operations import SetGain, SetOffset
from qililab.waveforms import Arbitrary, Square, Waveform
from qililab.yaml import yaml

if TYPE_CHECKING:
    from uuid import UUID

    from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix


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

    def set_crosstalk(self, crosstalk: CrosstalkMatrix) -> dict[str, float | list[float] | np.ndarray]:
        """Set the crosstalk compensation on the existing flux vector.

        Applies the crosstalk matrix inversion to convert target flux values into
        hardware bias values. Both scalar and array flux values are supported, allowing
        this method to be used for single operating points as well as sweep-based
        experiments. If a NonLinearCrosstalkMatrix is provided, nonlinear corrections
        are applied via its overridden flux_to_bias method.

        Any bus present in the crosstalk matrix but missing from the flux vector is
        initialised to zero. List values are converted to numpy arrays before processing.

        Args:
            crosstalk (CrosstalkMatrix): The crosstalk matrix to apply. Can be a linear
                CrosstalkMatrix or a NonLinearCrosstalkMatrix, in which case the nonlinear
                Bessel-series corrections are included in the bias computation.

        Returns:
            dict[str, float | list[float] | np.ndarray]: The computed bias vector keyed
                by bus name. Scalar flux inputs produce scalar bias outputs; array flux
                inputs produce array bias outputs.
        """
        self.crosstalk = crosstalk
        self.crosstalk_inverse = crosstalk.inverse()
        self.crosstalk_inverse.flux_offsets = self.crosstalk.flux_offsets

        for bus in self.crosstalk.matrix.keys():
            if bus not in self.flux_vector:
                self.flux_vector[bus] = 0
            if isinstance(self.flux_vector[bus], list):
                self.flux_vector[bus] = np.array(self.flux_vector[bus])

        return self.update_bias_vector()

    def update_bias_vector(self):
        if self.crosstalk:
            flux_dict = {bus: self.flux_vector[bus] for bus in self.crosstalk.matrix.keys()}
            self.bias_vector = self.flux_vector.copy()
            self.bias_vector.update(self.crosstalk.flux_to_bias(flux_dict))

            return self.bias_vector
        raise AttributeError("Cannot calcualte effective bias if Crosstalk is not set")

    def set_crosstalk_from_bias(
        self, crosstalk: CrosstalkMatrix, bias_vector: dict[str, float | list[float] | np.ndarray] | None = None
    ) -> dict[str, float | list[float] | np.ndarray]:
        """Set the crosstalk compensation on the existing flux vector. This function does the matrix product to calculate the correct flux

        Args:
            crosstalk (CrosstalkMatrix): crosstalk matrix to be applied

        """
        self.crosstalk = crosstalk

        if bias_vector:
            self.bias_vector = bias_vector.copy()
        if not self.bias_vector:
            self.bias_vector = self.flux_vector.copy()

        for bus_1 in self.crosstalk.matrix.keys():
            self.flux_vector[bus_1] = (
                sum(
                    (self.bias_vector[bus_2] * self.crosstalk.matrix[bus_1][bus_2])  # type: ignore
                    for bus_2 in self.crosstalk.matrix[bus_1].keys()
                )
                + self.crosstalk.flux_offsets[bus_1]
            )

        return self.flux_vector

    def to_dict(self) -> dict[str, float | list[float] | np.ndarray]:
        """To dictionary method, returns the vector's dictionary

        Returns:
            dict[str, float]: Flux vector dictionary
        """
        if self.bias_vector:
            return self.bias_vector
        return self.flux_vector

    def get_decomposed_vector(self, bus_list: list[str] | None = None) -> dict[str, "FluxVector"]:
        """Return dictionary with flux vector decomposed by variables, for each flux return a flux vector considering
        the rest of fluxes (or the rest of the fluxes from the bus_list if given) as 0.
        This is typically used to sum variables in flux vs flux Qprogram.

        Args:
            flux_dict (optional, list[str] | None): List of fluxes to be decomposed. Defaults to None

        Returns:
            dict[str, FluxVector]: Dictionary containing different flux vectors for each bus.
        """
        list_fluxes = {}
        if self.crosstalk:
            for bus in self.crosstalk.matrix.keys():
                flux_vector_copy = deepcopy(self)
                for zero_flux in self.crosstalk.matrix.keys():
                    if (bus_list is not None and bus in bus_list and zero_flux in bus_list and zero_flux != bus) or (
                        bus_list is None and zero_flux != bus
                    ):
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


class NonLinearFluxVector:
    @dataclass
    class VariableContext:
        label: str
        arr: np.ndarray
        loop_ref: int

    class VariableRegistry(dict):
        def __setitem__(self, label: str, context: "NonLinearFluxVector.VariableContext") -> None:
            if label in self:
                raise ValueError(f"Variable '{label}' is linked to another loop.\nUse exit_loop to eliminate context.")
            super().__setitem__(label, context)

    def __init__(self) -> None:
        self.offset: dict[str, float | Variable | VariableExpression] = {}
        self.gain: dict[str, float | Variable | VariableExpression] = {}
        self.buses: set[str] = set()
        self.crosstalk: CrosstalkMatrix | None = None

        self.loops: dict[int, ForLoop | Parallel] = {}
        self.loops_uuid: dict[int, UUID] = {}
        self.variables: NonLinearFluxVector.VariableRegistry = NonLinearFluxVector.VariableRegistry()
        self.curr_loop_id = 0

    def _set_offset(self, bus: str, value: float | Variable | VariableExpression):
        if bus not in self.buses:
            raise ValueError(f"The bus {bus} is not in crosstalk.")
        if isinstance(value, (Variable)):
            self._verify_variable_exists(value)

        self.offset[bus] = value

    def _set_gain(self, bus: str, value: float | Variable | VariableExpression):
        if bus not in self.buses:
            raise ValueError(f"The bus {bus} is not in crosstalk.")
        if isinstance(value, (Variable)):
            self._verify_variable_exists(value)

        self.gain[bus] = value

    def _verify_variable_exists(self, value: Variable | VariableExpression):
        if isinstance(value, VariableExpression):
            if isinstance(value.left, Variable):
                self._verify_variable_exists(value.left)
            if isinstance(value.right, Variable):
                self._verify_variable_exists(value.right)
            return
        if value.label not in self.variables:
            raise ValueError(
                f"Variable with label {value.label} hasn't been contextualized with a loop.\n"
                "Use set_loop to contextualize variables."
            )

    def set_element(self, element: SetGain | SetOffset):
        """Registers a gain or offset value for a bus.

        Stores element.gain in self.gain[bus] (SetGain) or element.offset_path0
        in self.offset[bus] (SetOffset).

        Args:
            element (SetGain | SetOffset): Operation carrying the target bus and value.

        Raises:
            ValueError: If element.bus is not in self.buses. self.buses is empty
                until set_crosstalk or set_crosstalk_from_bias has been called.
            ValueError: If the element contains a variable that has not been contextualized with set_loop.
        """
        if isinstance(element, SetGain):
            self._set_gain(element.bus, element.gain)
        elif isinstance(element, SetOffset):
            self._set_offset(element.bus, element.offset_path0)

    def set_loop(self, loop: Parallel | ForLoop):
        """Registers a loop ('s variable) to the sweep context.

        With n loops registered, the outputs of get_corrected_offsets and
        get_corrected_play are arrays of shape (len(loop_n), ..., len(loop_1)).
        Any self.offset or self.gain entry assigned to a Variable (or
        VariableExpression) of this loop will sweep over its corresponding dimension.

        Args:
            loop (Parallel | ForLoop): Loop to add to the sweep context.

        Raises:
            ValueError: If any of the loop's variable labels is already registered
                (duplicate variable across active loops).
        """
        if isinstance(loop, Parallel):
            for in_loop in loop.loops:
                if isinstance(in_loop, ForLoop):
                    self.variables[in_loop.variable.label] = self.VariableContext(
                        in_loop.variable.label,
                        np.arange(in_loop.start, in_loop.stop, in_loop.step),
                        self.curr_loop_id,
                    )
                elif isinstance(in_loop, Loop):
                    self.variables[in_loop.variable.label] = self.VariableContext(
                        in_loop.variable.label,
                        in_loop.values,
                        self.curr_loop_id,
                    )
        elif isinstance(loop, ForLoop):
            self.variables[loop.variable.label] = self.VariableContext(
                loop.variable.label,
                np.arange(loop.start, loop.stop, loop.step),
                self.curr_loop_id,
            )
        self.loops[self.curr_loop_id] = loop
        self.loops_uuid[self.curr_loop_id] = loop.uuid
        self.curr_loop_id += 1

    def exit_loop(self, loop: Parallel | ForLoop):
        """Removes a loop from the sweep context and resolves all Variable references.

        Any self.offset or self.gain entry assigned to a Variable (or VariableExpression)
        belonging to this loop is replaced with the loop's last value. For a
        Parallel loop, all of its variables are resolved.

        Args:
            loop (Parallel | ForLoop): Loop to remove from the sweep context.
        """
        labels: list[str] = []
        if isinstance(loop, ForLoop):
            labels.append(loop.variable.label)
        elif isinstance(loop, Parallel):
            for in_loop in loop.loops:
                if isinstance(in_loop, (ForLoop, Loop)):
                    labels.append(in_loop.variable.label)

        loop_id: int | None = next(
            (self.variables[label].loop_ref for label in labels if label in self.variables),
            None,
        )
        if loop_id is None:
            return

        # Last value for every variable that belongs to this loop_id
        last_values: dict[str, float] = {
            label: float(vc.arr[-1]) for label, vc in self.variables.items() if vc.loop_ref == loop_id
        }

        for bus in self.offset:
            self.offset[bus] = self._substitute_last_values(self.offset[bus], last_values)
        for bus in self.gain:
            self.gain[bus] = self._substitute_last_values(self.gain[bus], last_values)

        # Clean up all VariableContexts for this loop_id and the loop itself
        for label in [lbl for lbl, vc in self.variables.items() if vc.loop_ref == loop_id]:
            del self.variables[label]

    def _substitute_last_values(
        self,
        expr: float | Variable | VariableExpression,
        last_values: dict[str, float],
    ) -> float | Variable | VariableExpression:
        if isinstance(expr, VariableExpression):
            left = last_values.get(expr.left.label, expr.left) if isinstance(expr.left, Variable) else expr.left
            right = last_values.get(expr.right.label, expr.right) if isinstance(expr.right, Variable) else expr.right
            if not isinstance(left, Variable) and not isinstance(right, Variable):
                return float(left + right) if expr.operator == "+" else float(left - right)
            return VariableExpression(left, expr.operator, right)
        if isinstance(expr, Variable):
            return last_values.get(expr.label, expr)
        return expr

    def get_corrected_play(self, waveforms: dict[str, Waveform]) -> dict[str, np.ndarray]:
        """Computes the crosstalk-compensated waveform per bus.

        For each bus, computes the total flux as waveform * gain + offset, applies the
        crosstalk matrix inversion, then subtracts the corrected offset to isolate
        the (play) component. Buses absent from waveforms are treated as
        Square(amplitude=0, duration=<duration of other waveforms>).

        Precondition: self.gain must be 1 for all played buses before calling this
        method, as the gain is folded into the output waveform.

        Args:
            waveforms (dict[str, Waveform]): Simultaneous waveforms to play, keyed by
                bus. Buses not present are treated as silent (amplitude=0).

        Raises:
            AttributeError: If set_crosstalk has not been called.
            ValueError: If any waveforms have different durations.

        Returns:
            dict[str, Square | Arbitrary]: Per-bus waveforms. Square is used when
                the waveform samples are within a tolerance of a constant value;
                Arbitrary otherwise.
        """
        if self.crosstalk is None:
            raise AttributeError(
                "No crosstalk has been set.\nYou can set it using set_crosstalk or set_crosstalk_from_bias"
            )
        durations = {bus: w.get_duration() for bus, w in waveforms.items()}
        if len(set(durations.values())) > 1:
            raise ValueError(f"All waveforms must have the same duration, got: {durations}")
        dur = next(iter(durations.values()))

        gain_flat = self._generate_matrix_values(self.gain)
        offset_flat = self._generate_matrix_values(self.offset)

        bias_offset: dict[str, np.ndarray] = self.crosstalk.flux_to_bias(offset_flat)  # type: ignore[assignment]
        unique_loop_refs, loop_lengths = self._loop_structure()
        shape = tuple(loop_lengths[lr] for lr in unique_loop_refs) if unique_loop_refs else (1,)
        total_length = int(np.prod(list(loop_lengths.values()))) if loop_lengths else 1

        # combined[bus][k * dur + t] = gain_flat[bus][k] * envelope[t] + offset_flat[bus][k]
        # Buses without a waveform contribute only their offset (play = 0).
        combined_flux: dict[str, np.ndarray] = {}
        for bus in self.buses:
            if bus in waveforms:
                combined_flux[bus] = (
                    np.outer(gain_flat[bus], waveforms[bus].envelope()) + offset_flat[bus][:, np.newaxis]
                ).reshape(-1)
            else:
                combined_flux[bus] = np.repeat(offset_flat[bus], dur)
        bias_combined: dict[str, np.ndarray] = self.crosstalk.flux_to_bias(combined_flux)  # type: ignore[assignment]

        result: dict[str, np.ndarray] = {}
        for bus in self.buses:
            correction = bias_combined[bus].reshape(total_length, dur) - bias_offset[bus][:, np.newaxis]
            waveform_arr = np.empty(total_length, dtype=object)
            for k in range(total_length):
                env = correction[k]
                if np.allclose(env, env[0]):
                    waveform_arr[k] = Square(amplitude=float(env[0]), duration=dur)
                else:
                    waveform_arr[k] = Arbitrary(samples=env)
            result[bus] = waveform_arr.reshape(shape)
        return result

    def get_corrected_offsets(self) -> dict[str, np.ndarray]:
        """Computes the crosstalk-compensated offset for all loop values.

        Applies the crosstalk matrix to self.offset, sweeping over any registered loop
        variables. With n loops the returned arrays have shape (len(loop_n), ..., len(loop_1));
        with no loops each array has length 1 containing the current scalar offset value.

        Raises:
            AttributeError: If set_crosstalk has not been called.

        Returns:
            dict[str, np.ndarray]: Per-bus arrays of compensated offset values.
        """

        if self.crosstalk is None:
            raise AttributeError(
                "No crosstalk has been set.\nYou can set it using set_crosstalk or set_crosstalk_from_bias"
            )
        flat = self._generate_matrix_values(self.offset)
        biases: dict[str, np.ndarray] = self.crosstalk.flux_to_bias(flat)  # type: ignore[assignment]
        unique_loop_refs, loop_lengths = self._loop_structure()
        shape = tuple(loop_lengths[lr] for lr in unique_loop_refs) if unique_loop_refs else (1,)
        return {bus: arr.reshape(shape) for bus, arr in biases.items()}

    def _loop_structure(self) -> tuple[list[int], dict[int, int]]:
        """Returns (unique_loop_refs sorted high→low, loop_lengths per loop_ref)."""
        unique_loop_refs = sorted(
            {vc.loop_ref for vc in self.variables.values()},
            reverse=True,
        )
        loop_lengths: dict[int, int] = {
            lr: len(next(vc for vc in self.variables.values() if vc.loop_ref == lr).arr) for lr in unique_loop_refs
        }
        if not loop_lengths:
            return [-1], {-1: 1}
        return unique_loop_refs, loop_lengths

    def _generate_matrix_values(
        self, values: dict[str, float | Variable | VariableExpression]
    ) -> dict[str, np.ndarray]:
        unique_loop_refs, loop_lengths = self._loop_structure()
        total_length = int(np.prod(list(loop_lengths.values()))) if loop_lengths else 1

        result: dict[str, np.ndarray] = {}
        for bus, val in values.items():
            if isinstance(val, VariableExpression):
                result[bus] = np.asarray(self._evaluate_expr(val, unique_loop_refs, loop_lengths), dtype=float)
            elif isinstance(val, Variable):
                result[bus] = self._expand_variable(val, unique_loop_refs, loop_lengths)
            else:
                result[bus] = np.full(total_length, float(val))
        return result

    def _expand_variable(
        self,
        var: Variable,
        unique_loop_refs: list[int],
        loop_lengths: dict[int, int],
    ) -> np.ndarray:
        """Expand a Variable to a 1D array covering all loop combinations."""
        var_ctx = self.variables[var.label]
        pos = unique_loop_refs.index(var_ctx.loop_ref)
        inner = int(
            np.prod([loop_lengths[unique_loop_refs[j]] for j in range(pos + 1, len(unique_loop_refs))])
            if pos + 1 < len(unique_loop_refs)
            else 1
        )
        outer = int(np.prod([loop_lengths[unique_loop_refs[j]] for j in range(pos)]) if pos > 0 else 1)
        return np.tile(np.repeat(var_ctx.arr, inner), outer)

    def _evaluate_expr(
        self,
        expr: Variable | VariableExpression | int | float,
        unique_loop_refs: list[int],
        loop_lengths: dict[int, int],
    ) -> np.ndarray | float:
        if isinstance(expr, VariableExpression):
            left = self._evaluate_expr(expr.left, unique_loop_refs, loop_lengths)
            right = self._evaluate_expr(expr.right, unique_loop_refs, loop_lengths)
            if expr.operator == "+":
                return left + right
            if expr.operator == "-":
                return left - right
            raise ValueError(f"Unsupported VariableExpression operator: {expr.operator}")
        if isinstance(expr, Variable):
            return self._expand_variable(expr, unique_loop_refs, loop_lengths)
        return float(expr)  # plain int / float — numpy broadcasts with arrays above

    def set_crosstalk(self, crosstalk: CrosstalkMatrix):
        """Attaches a crosstalk matrix and populates the bus registry.

        Sets self.crosstalk to the provided matrix and updates self.buses with all
        bus names from it. Any bus missing from self.offset is initialised to 0;
        any bus missing from self.gain is initialised to 1. Pre-existing values
        are preserved.

        Args:
            crosstalk (CrosstalkMatrix): The crosstalk matrix to attach.
        """
        self.crosstalk = crosstalk
        self.buses = set(self.crosstalk.matrix.keys())
        for bus in self.buses:
            if bus not in self.offset:
                self.offset[bus] = 0.0
            if bus not in self.gain:
                self.gain[bus] = 1.0

    def set_crosstalk_from_bias(
        self, crosstalk: CrosstalkMatrix, bias_vector: dict[str, float | np.ndarray]
    ) -> dict[str, float | Variable | VariableExpression]:
        """Computes per-bus flux values from hardware bias values using the linear crosstalk matrix.

        Calls set_crosstalk internally to attach the matrix and initialise the bus registry,
        then computes self.offset = crosstalk_matrix @ bias_vector using only the linear
        component of the matrix. Nonlinear corrections are not applied even when a
        NonLinearCrosstalkMatrix is provided.

        Args:
            crosstalk (CrosstalkMatrix): The crosstalk matrix to attach. May be a linear
                CrosstalkMatrix or a NonLinearCrosstalkMatrix; only its linear part is used.
            bias_vector (dict[str, float | Variable | VariableExpression]): Hardware bias
                values keyed by bus name.

        Returns:
            dict[str, float | list[float] | np.ndarray]: The computed flux values stored
                in self.offset, keyed by bus name.
        """
        self.set_crosstalk(crosstalk)
        crosstalk = cast("CrosstalkMatrix", self.crosstalk)
        for bus_1 in crosstalk.matrix.keys():
            self.offset[bus_1] = (
                sum(
                    (bias_vector[bus_2] * crosstalk.matrix[bus_1][bus_2])  # type: ignore
                    for bus_2 in crosstalk.matrix[bus_1].keys()
                )
                + crosstalk.flux_offsets[bus_1]
            )

        return self.offset
