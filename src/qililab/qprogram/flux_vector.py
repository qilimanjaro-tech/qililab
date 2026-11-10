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

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import numpy as np
from qprogram import BinaryOp, Constant, Expression, Range, UnaryOp, Variable
from qprogram.blocks import Parallel, Sweep
from qprogram.operations import SetGain, SetOffset
from qprogram.waveforms import Arbitrary, Square, Waveform

from qililab.qprogram.blocks import for_loop_iterations
from qililab.yaml import yaml

if TYPE_CHECKING:
    from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix


def sweep_points(sweep: Sweep) -> np.ndarray:
    """The values a sweep takes when it runs, as the Qblox compiler runs it.

    A ``Range`` runs like a for_loop, from ``start`` to its last point in ``for_loop_iterations`` evenly spread points,
    its last point being ``stop`` when the range lands on it. Any other source runs over its own values.

    Args:
        sweep (Sweep): The sweep.

    Returns:
        np.ndarray: Its values, in order.
    """
    source = sweep.source
    if not isinstance(source, Range):
        return np.asarray(source.values(), dtype=float)
    last = source.start + source.step * (source.length() - 1)
    if math.isclose(last, source.stop, rel_tol=1e-9, abs_tol=1e-12):
        last = source.stop
    return np.linspace(source.start, last, max(for_loop_iterations(source.start, last, source.step), 0))


def _as_number(value: float | Expression) -> float | Expression:
    """Return a ``Constant`` as its number, and anything else unchanged.

    Args:
        value (float | Expression): The value.

    Returns:
        float | Expression: The number held by a constant, else ``value``.
    """
    return value.value if isinstance(value, Constant) else value


def _as_expression(value: float | Expression) -> Expression:
    """Return a number as a ``Constant``, and an expression unchanged.

    Args:
        value (float | Expression): The value.

    Returns:
        Expression: The expression.
    """
    return value if isinstance(value, Expression) else Constant(float(value))


@yaml.register_class
class FluxVector:
    """Class to represent a flux vector. This is a dictionary of bus[flux] values"""

    def __init__(self) -> None:
        self.flux_vector: dict[str, float | list[float] | np.ndarray] = {}
        self.bias_vector: dict[str, float | list[float] | np.ndarray] = {}
        self.crosstalk: CrosstalkMatrix | None = None
        self._crosstalk_inverse: CrosstalkMatrix | None = None

    @property
    def crosstalk_inverse(self) -> "CrosstalkMatrix | None":
        """Inverse of the attached crosstalk matrix, computed lazily on first access."""
        if self._crosstalk_inverse is None and self.crosstalk is not None:
            inverse = self.crosstalk.inverse()
            inverse.flux_offsets = self.crosstalk.flux_offsets
            self._crosstalk_inverse = inverse
        return self._crosstalk_inverse

    @crosstalk_inverse.setter
    def crosstalk_inverse(self, value: "CrosstalkMatrix | None") -> None:
        self._crosstalk_inverse = value

    def __getitem__(self, bus: str) -> float | list[float] | np.ndarray:
        """Given a bus, returns its corresponding flux

        Args:
            bus (str): The bus for which to get the flux values.

        Returns:
            float | list[float] | np.ndarray: Flux value for the given bus
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
        self._crosstalk_inverse = None

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

        Returns:
            dict[str, float | list[float] | np.ndarray]: The computed flux vector keyed
                by bus name. Scalar bias inputs produce scalar flux outputs; array bias
                inputs produce array flux outputs.
        """
        self.crosstalk = crosstalk

        if bias_vector:
            self.bias_vector = bias_vector.copy()
        if not self.bias_vector:
            self.bias_vector = self.flux_vector.copy()

        buses = crosstalk._sorted_buses()
        matrix = crosstalk.to_array()
        offsets = np.array([crosstalk.flux_offsets.get(bus, 0.0) for bus in buses])
        bias_values = [self.bias_vector[bus] for bus in buses]

        # Scalar Flux
        if all(isinstance(value, (int, float, np.number)) for value in bias_values):
            flux = matrix @ np.array(bias_values, dtype=float) + offsets
            for bus, value in zip(buses, flux):
                self.flux_vector[bus] = float(value)
        # Array Flux
        else:
            length = max(np.asarray(value).size for value in bias_values)
            bias_stack = np.stack([np.broadcast_to(np.asarray(value, dtype=float), length) for value in bias_values])
            flux = matrix @ bias_stack + offsets[:, np.newaxis]
            for bus, vector in zip(buses, flux):
                self.flux_vector[bus] = vector

        return self.flux_vector

    def to_dict(self) -> dict[str, float | list[float] | np.ndarray]:
        """To dictionary method, returns the vector's dictionary

        Returns:
            dict[str, float | list[float] | np.ndarray]: Flux vector dictionary
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
        list_fluxes: dict[str, "FluxVector"] = {}
        if not self.crosstalk:
            return list_fluxes

        buses = list(self.crosstalk.matrix.keys())
        for bus in buses:
            if bus_list is not None and bus not in bus_list:
                continue
            decomposed_flux = dict(self.flux_vector)
            for zero_flux in buses:
                if zero_flux != bus and (bus_list is None or zero_flux in bus_list):
                    decomposed_flux[zero_flux] = 0
            decomposed = FluxVector.from_dict(decomposed_flux)
            # Share the crosstalk matrix (read-only here) rather than deep-copying it per bus.
            decomposed.set_crosstalk(self.crosstalk)
            list_fluxes[bus] = decomposed
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
    """Flux of each crosstalk bus over every point of the loops sweeping it, for non-linear crosstalk compensation.

    The offset and gain of each bus are numbers or expressions of loop variables. Registering the loops sweeping those
    variables (``set_loop``) gives the corrected offsets and waveforms at every point of the loops.
    """

    @dataclass
    class VariableContext:
        """The values a loop variable takes, and the loop setting it.

        Attributes:
            label (str): The id of the variable.
            arr (np.ndarray): Its values, in order.
            loop_ref (int): The index of its loop in ``NonLinearFluxVector.loops``.
        """

        label: str
        arr: np.ndarray
        loop_ref: int

    class VariableRegistry(dict):
        """The registered loop variables, by id. A variable can only be registered once."""

        def __setitem__(self, label: str, context: "NonLinearFluxVector.VariableContext") -> None:
            if label in self:
                raise ValueError(f"Variable '{label}' is linked to another loop.\nUse exit_loop to eliminate context.")
            super().__setitem__(label, context)

    def __init__(self) -> None:
        self.offset: dict[str, float | Expression] = {}
        self.gain: dict[str, float | Expression] = {}
        self.buses: set[str] = set()
        self.crosstalk: CrosstalkMatrix | None = None

        self.loops: dict[int, Sweep | Parallel] = {}
        self.variables: NonLinearFluxVector.VariableRegistry = NonLinearFluxVector.VariableRegistry()
        self.curr_loop_id = 0

    def _set_offset(self, bus: str, value: float | Expression) -> None:
        if bus not in self.buses:
            raise ValueError(f"The bus {bus} is not in crosstalk.")
        if isinstance(value, Expression):
            self._verify_variable_exists(value)

        self.offset[bus] = value

    def _set_gain(self, bus: str, value: float | Expression) -> None:
        if bus not in self.buses:
            raise ValueError(f"The bus {bus} is not in crosstalk.")
        if isinstance(value, Expression):
            self._verify_variable_exists(value)

        self.gain[bus] = value

    def _verify_variable_exists(self, value: Expression) -> None:
        for variable in sorted(value.variables(), key=lambda variable: variable.id):
            if variable.id not in self.variables:
                raise ValueError(
                    f"Variable with label {variable.id} hasn't been contextualized with a loop.\n"
                    "Use set_loop to contextualize variables."
                )

    def has_loop(self, block: object) -> bool:
        """Whether ``block`` is one of the registered loops (the very block, not an equal one).

        Args:
            block (object): The block.

        Returns:
            bool: True if ``block`` was registered with ``set_loop``.
        """
        return any(loop is block for loop in self.loops.values())

    def set_element(self, element: SetGain | SetOffset) -> None:
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

    def set_loop(self, loop: Sweep | Parallel) -> None:
        """Registers a loop ('s variable) to the sweep context.

        With n loops registered, the outputs of get_corrected_offsets and
        get_corrected_play are arrays of shape (len(loop_n), ..., len(loop_1)).
        Any self.offset or self.gain entry assigned to a Variable (or an
        expression of it) of this loop will sweep over its corresponding dimension.

        Args:
            loop (Sweep | Parallel): Loop to add to the sweep context.

        Raises:
            ValueError: If the loops of a Parallel don't have the same length, or if any of the loop's variables is
                already registered (duplicate variable across active loops).
        """
        if isinstance(loop, Parallel):
            loop_points = [sweep_points(in_loop) for in_loop in loop.loops]
            loop_iterations = [len(points) for points in loop_points]
            if not np.allclose(loop_iterations, loop_iterations[0]):
                raise ValueError("All the loops in a parallel loop should have the same length")
            for points, in_loop in zip(loop_points, loop.loops):
                self.variables[in_loop.variable.id] = self.VariableContext(
                    in_loop.variable.id, points, self.curr_loop_id
                )
        elif isinstance(loop, Sweep):
            self.variables[loop.variable.id] = self.VariableContext(
                loop.variable.id, sweep_points(loop), self.curr_loop_id
            )
        self.loops[self.curr_loop_id] = loop
        self.curr_loop_id += 1

    def exit_loop(self, loop: Sweep | Parallel) -> None:
        """Removes a loop from the sweep context and resolves all Variable references.

        Any self.offset or self.gain entry assigned to a Variable (or an expression of it)
        belonging to this loop is replaced with the loop's last value. For a
        Parallel loop, all of its variables are resolved.

        Args:
            loop (Sweep | Parallel): Loop to remove from the sweep context.
        """
        labels: list[str] = []
        if isinstance(loop, Sweep):
            labels.append(loop.variable.id)
        elif isinstance(loop, Parallel):
            labels.extend(in_loop.variable.id for in_loop in loop.loops)

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
        expr: float | Expression,
        last_values: dict[str, float],
    ) -> float | Expression:
        """Replace the variables of ``last_values`` by their value, folding a sum or difference of two numbers.

        Args:
            expr (float | Expression): The offset or gain.
            last_values (dict[str, float]): The value of each variable to replace, by id.

        Returns:
            float | Expression: The offset or gain with those variables replaced.
        """
        if isinstance(expr, BinaryOp):
            left = _as_number(self._substitute_last_values(expr.left, last_values))
            right = _as_number(self._substitute_last_values(expr.right, last_values))
            if not isinstance(left, Expression) and not isinstance(right, Expression) and expr.op in ("+", "-"):
                return float(left + right) if expr.op == "+" else float(left - right)
            return BinaryOp(expr.op, _as_expression(left), _as_expression(right))
        if isinstance(expr, UnaryOp):
            operand = _as_number(self._substitute_last_values(expr.operand, last_values))
            if not isinstance(operand, Expression) and expr.op in ("+", "-"):
                return float(operand) if expr.op == "+" else -float(operand)
            return UnaryOp(expr.op, _as_expression(operand))
        if isinstance(expr, Variable):
            return last_values.get(expr.id, expr)
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
        if not waveforms:
            raise ValueError(
                "The 'waveforms' dictionary is empty.\nIf you want the offsets use `get_corrected_offsets` instead"
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

    def _generate_matrix_values(self, values: dict[str, float | Expression]) -> dict[str, np.ndarray]:
        unique_loop_refs, loop_lengths = self._loop_structure()
        total_length = int(np.prod(list(loop_lengths.values()))) if loop_lengths else 1

        result: dict[str, np.ndarray] = {}
        for bus, val in values.items():
            if isinstance(val, Variable):
                result[bus] = self._expand_variable(val, unique_loop_refs, loop_lengths)
            elif isinstance(val, Expression):
                result[bus] = np.asarray(self._evaluate_expr(val, unique_loop_refs, loop_lengths), dtype=float)
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
        var_ctx = self.variables[var.id]
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
        expr: Expression | int | float,
        unique_loop_refs: list[int],
        loop_lengths: dict[int, int],
    ) -> np.ndarray | float:
        """Evaluate an offset or gain over all loop combinations.

        Args:
            expr (Expression | int | float): The offset or gain: a number, a variable, or a sum, difference or negation
                of those.
            unique_loop_refs (list[int]): The registered loops, sorted high to low.
            loop_lengths (dict[int, int]): The length of each registered loop.

        Returns:
            np.ndarray | float: Its values, as a 1D array covering all loop combinations, or a number.

        Raises:
            ValueError: If the expression uses another operation than a sum, a difference or a sign.
        """
        if isinstance(expr, BinaryOp):
            left = self._evaluate_expr(expr.left, unique_loop_refs, loop_lengths)
            right = self._evaluate_expr(expr.right, unique_loop_refs, loop_lengths)
            if expr.op == "+":
                return left + right
            if expr.op == "-":
                return left - right
            raise ValueError(f"Unsupported expression operator: {expr.op}")
        if isinstance(expr, UnaryOp):
            operand = self._evaluate_expr(expr.operand, unique_loop_refs, loop_lengths)
            if expr.op == "+":
                return operand
            if expr.op == "-":
                return -operand
            raise ValueError(f"Unsupported expression operator: {expr.op}")
        if isinstance(expr, Variable):
            return self._expand_variable(expr, unique_loop_refs, loop_lengths)
        if isinstance(expr, Constant):
            return float(expr.value)
        if isinstance(expr, Expression):
            raise ValueError(f"Unsupported expression: {expr!r}")
        # plain int / float — numpy broadcasts with arrays above
        return float(expr)

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
    ) -> dict[str, float | Expression]:
        """Computes per-bus flux values from hardware bias values using the linear crosstalk matrix.

        Calls set_crosstalk internally to attach the matrix and initialise the bus registry,
        then computes self.offset = crosstalk_matrix @ bias_vector using only the linear
        component of the matrix. Nonlinear corrections are not applied even when a
        NonLinearCrosstalkMatrix is provided.

        Args:
            crosstalk (CrosstalkMatrix): The crosstalk matrix to attach. May be a linear
                CrosstalkMatrix or a NonLinearCrosstalkMatrix; only its linear part is used.
            bias_vector (dict[str, float | np.ndarray]): Hardware bias
                values keyed by bus name.

        Returns:
            dict[str, float | list[float] | np.ndarray]: The computed flux values stored
                in self.offset, keyed by bus name.
        """
        self.set_crosstalk(crosstalk)
        crosstalk = cast("CrosstalkMatrix", self.crosstalk)

        buses = crosstalk._sorted_buses()
        matrix = crosstalk.to_array()
        offsets = np.array([crosstalk.flux_offsets.get(bus, 0.0) for bus in buses])
        bias_values = [bias_vector[bus] for bus in buses]

        # Scalar Flux
        if all(isinstance(value, (int, float, np.number)) for value in bias_values):
            flux = matrix @ np.array(bias_values, dtype=float) + offsets
            for bus, value in zip(buses, flux):
                self.offset[bus] = float(value)
        # Array Flux
        else:
            length = max(np.asarray(value).size for value in bias_values)
            bias_stack = np.stack([np.broadcast_to(np.asarray(value, dtype=float), length) for value in bias_values])
            flux = matrix @ bias_stack + offsets[:, np.newaxis]
            for bus, vector in zip(buses, flux):
                self.offset[bus] = vector

        return self.offset
