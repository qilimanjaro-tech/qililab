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
"""The crosstalk compensation behind ``QProgram.with_crosstalk_qblox`` and ``QProgram.with_crosstalk_qdac``."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import TYPE_CHECKING, TypeGuard

import numpy as np
from qprogram import RESERVED_KEYWORDS, Expression, Range, Variable
from qprogram.blocks import Block, Parallel, Sweep
from qprogram.operations import Measure, Play, SetGain, SetOffset, Sync, Wait
from qprogram.waveforms import Arbitrary, FlatTop, IQWaveform, Square, Waveform
from qprogram_qblox import Acquire
from qprogram_qdac import Play as QdacPlay
from qprogram_qdac import SetOffset as QdacSetOffset

from qililab.qprogram.blocks import ForLoop, IfTrigger
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, NonLinearCrosstalkMatrix
from qililab.qprogram.flux_vector import FluxVector, NonLinearFluxVector, sweep_points
from qililab.qprogram.operations.measure_reset import MeasureReset
from qililab.qprogram.operations.play import QbloxPlay
from qililab.qprogram.utils_crosstalk import CrosstalkElements, NonLinearFlagState, operation_key

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qprogram.operations import Operation

    from qililab.qprogram.qprogram import QProgram

QbloxPlayOperation = Play | QbloxPlay
"""A play on a Qblox bus: ``qp.play`` or ``qp.qblox.play``."""

QbloxFluxOperation = Play | QbloxPlay | SetOffset | SetGain
"""An operation the Qblox crosstalk compensation rewrites when its bus is in the crosstalk matrix."""

_QBLOX_PLAYS = (Play, QbloxPlay)
_PLAYS = (Play, QbloxPlay, QdacPlay)


def _has_named_waveform(element: Operation) -> bool:
    """Whether ``element`` still holds a waveform or weights given by name, to be resolved by a calibration.

    Such an operation is what qililab's ``PlayWithCalibratedWaveform``, ``MeasureWithCalibrated*``,
    ``AcquireWithCalibratedWeights`` and ``MeasureResetCalibrated`` were, and crosstalk compensation leaves it alone as
    it left those.

    Args:
        element (Operation): The operation.

    Returns:
        bool: True if one of its waveforms or weights is a name.
    """
    return any(isinstance(getattr(element, attribute, None), str) for attribute in element.WAVEFORM_ATTRS)


def _is_qblox_play(element: Block | Operation) -> TypeGuard[Play | QbloxPlay]:
    """Whether ``element`` is a ``qp.play`` or ``qp.qblox.play`` with a concrete waveform.

    Args:
        element (Block | Operation): The node.

    Returns:
        bool: True for a Qblox play the compensation can read.
    """
    return isinstance(element, _QBLOX_PLAYS) and not _has_named_waveform(element)


def _passes_time(element: Block | Operation) -> bool:
    """Whether ``element`` lets time pass on the flux buses, so the operations before and after it are not simultaneous.

    That is a ``wait``, an acquisition or measurement, or a play on a bus outside the crosstalk matrix (checked by the
    caller).

    Args:
        element (Block | Operation): The node.

    Returns:
        bool: True for a wait, a concrete acquisition or a concrete measurement.
    """
    if isinstance(element, Wait):
        return True
    return isinstance(element, (Acquire, Measure)) and not _has_named_waveform(element)


def _is_range_sweep(block: object) -> bool:
    """Whether ``block`` is a sweep over a ``Range``, the loop ``qp.for_loop`` and ``from_range`` build.

    Args:
        block (object): The node.

    Returns:
        bool: True for a ``Sweep`` whose source is a ``Range``.
    """
    return isinstance(block, Sweep) and isinstance(block.source, Range)


def _header_loops(block: Block) -> list[Sweep]:
    """The loops a block advances: a ``Parallel``'s loops, a ``Sweep`` itself, none for any other block.

    Args:
        block (Block): The block.

    Returns:
        list[Sweep]: Its loops.
    """
    if isinstance(block, Parallel):
        return list(block.loops)
    if isinstance(block, Sweep):
        return [block]
    return []


def _flux_offset_value(operation: SetOffset | SetGain) -> float | Expression:
    """The value carried by a ``SetOffset`` (path 0) or a ``SetGain``.

    Args:
        operation (SetOffset | SetGain): The operation.

    Returns:
        float | Expression: Its offset or gain.
    """
    return operation.offset_path0 if isinstance(operation, SetOffset) else operation.gain


def _set_flux_offset_value(operation: SetOffset | SetGain, value: float | Expression) -> None:
    """Set the value carried by a ``SetOffset`` (path 0) or a ``SetGain``.

    Args:
        operation (SetOffset | SetGain): The operation.
        value (float | Expression): Its new offset or gain.
    """
    if isinstance(operation, SetOffset):
        operation.offset_path0 = value
    else:
        operation.gain = value


def _element_variable(element: QbloxFluxOperation) -> Variable | None:
    """The variable set by a ``SetGain`` or a ``SetOffset``, if it sets one.

    Args:
        element (QbloxFluxOperation): The operation.

    Returns:
        Variable | None: The variable, or None for a play or a fixed value.
    """
    if isinstance(element, SetGain) and isinstance(element.gain, Variable):
        return element.gain
    if isinstance(element, SetOffset) and isinstance(element.offset_path0, Variable):
        return element.offset_path0
    return None


def _ends_in_if_trigger(element: Block | Operation) -> bool:
    """Whether ``element`` is a ``qp.if_trigger()`` block, or a block whose own last element does (recursively).

    Args:
        element (Block | Operation): The node.

    Returns:
        bool: True if the node ends in an ``IfTrigger``.
    """
    if isinstance(element, IfTrigger):
        return True
    if isinstance(element, Block) and element.elements:
        return _ends_in_if_trigger(element.elements[-1])
    return False


def _sanitize_id(name: str) -> str:
    """Turn ``name`` into a valid variable id: ``[A-Za-z_][A-Za-z0-9_]*``.

    Args:
        name (str): The name, such as a bus alias followed by a variable id.

    Returns:
        str: ``name`` with every other character replaced by ``_``, prefixed by ``_`` if it starts with a digit.
    """
    sanitized = re.sub(r"[^A-Za-z0-9_]", "_", name) or "var"
    return f"_{sanitized}" if sanitized[0].isdigit() else sanitized


def _shift_suffix(constant: float) -> str:
    """The id suffix of a loop shifted by ``constant``: ``_plus_0p1`` for ``+0.1``, ``_minus_2em05`` for ``-2e-05``.

    Args:
        constant (float): The shift.

    Returns:
        str: The suffix.
    """
    text = f"{constant:+g}".replace("+", "_plus_").replace("-", "_minus_").replace(".", "p")
    return text.replace("e_minus_", "em").replace("e_plus_", "ep")


class _QbloxCrosstalkCompensation:
    """Rewrites a QProgram, in place, so the flux the crosstalk matrix maps it to is the flux the program sets.

    Every ``set_offset``, ``set_gain`` and ``play`` (``qp.play`` or ``qp.qblox.play``) on a bus of the crosstalk matrix
    is replaced by the compensated operations on all the buses of the matrix. Operations set together (no time passing
    between them) are compensated together. A loop sweeping a flux is replaced by loops sweeping the compensated
    biases, in lockstep.

    With a ``NonLinearCrosstalkMatrix``, the loops sweeping a flux are unrolled instead, and each point gets its own
    offsets and waveforms.

    Args:
        program (QProgram): The QProgram to rewrite. It is modified.
        crosstalk (CrosstalkMatrix): The crosstalk matrix.
    """

    def __init__(self, program: QProgram, crosstalk: CrosstalkMatrix) -> None:
        self.program = program
        self.crosstalk = crosstalk
        self.bus_variable_map: dict[tuple[Variable | float | None, str], Variable] = {}
        self.block_variables: dict[Variable | float | None, list[Variable]] = {}
        self.parallel_loops: dict[Variable, list[Sweep]] = {}
        self.active_loops: list[Sweep | Parallel] = []
        self.loop_depths: list[int] = []
        self.bus_loop_depth: dict[str, int] = {}
        self.constant_bus_variables: set[Variable] = set()
        # Compensated SetOffset/SetGain (by id) -> (own loop terms, constant bias, buses the user set in its group).
        # The final value is assembled by `assemble_flux_operations` once every block has been rewritten.
        self.flux_terms: dict[int, tuple[list[Variable], float, set[str]]] = {}
        # (operation class, loop variable) -> crosstalk buses that variable sweeps.
        self.variable_buses: dict[tuple[type, Variable], set[str]] = {}
        # Compensated loop variable -> the user's loop variable it follows.
        self.bus_variable_origin: dict[Variable, Variable] = {}
        # A compensated loop left alone in its block (by id) -> (that loop, shifted copies to run with it).
        self.extra_loops: dict[int, tuple[Sweep, list[Sweep]]] = {}
        self.taken_ids: set[str] = {variable.id for variable in program.variables} | {
            variable.id for variable in program.body.variables()
        }

        self.non_lin_flux_vector: NonLinearFluxVector | None = None
        if isinstance(crosstalk, NonLinearCrosstalkMatrix):
            self.non_lin_flux_vector = NonLinearFluxVector()
            self.non_lin_flux_vector.set_crosstalk(crosstalk)
        self.non_lin_play_waveforms: list[dict[str, np.ndarray]] = []
        self.non_lin_offsets: list[dict[str, np.ndarray]] = []

    def run(self) -> None:
        """Rewrite the program."""
        self.traverse(self.program.body)
        if self.non_lin_flux_vector is not None:
            corrected_elements, _ = self.handle_non_linear(
                list(self.program.body.elements),
                self.non_lin_flux_vector,
                self.non_lin_offsets,
                self.non_lin_play_waveforms,
            )
            self.program.body.elements[:] = corrected_elements
        else:
            self.bus_variable_origin = {
                bus_variable: variable
                for (variable, _), bus_variable in self.bus_variable_map.items()
                if isinstance(variable, Variable)
            }
            self.assemble_flux_operations(self.program.body, {}, [], {})
            self.attach_extra_loops(self.program.body)

    def new_variable(self, name: str) -> Variable:
        """Create a variable with an id derived from ``name`` that no other variable of the program uses.

        Args:
            name (str): The name to derive the id from.

        Returns:
            Variable: The new variable. It is not declared on the program yet.
        """
        base = _sanitize_id(name)
        variable_id, suffix = base, 2
        while variable_id in self.taken_ids or variable_id in RESERVED_KEYWORDS:
            variable_id, suffix = f"{base}_{suffix}", suffix + 1
        self.taken_ids.add(variable_id)
        return Variable(variable_id)

    def declare(self, variable: Variable) -> None:
        """Declare ``variable`` on the program, if it is not declared yet.

        Args:
            variable (Variable): The variable.
        """
        if variable not in self.program.variables:
            self.program._variables.append(variable)

    def traverse(self, block: Block, flux_vector: dict[str, FluxVector] | None = None) -> None:
        """Traverse all the elements of ``block``, rewriting loops and the ``play``, ``set_offset`` and ``set_gain``.

        Args:
            block (Block): The block.
            flux_vector (dict[str, FluxVector] | None, optional): The flux vectors of the enclosing block, per
                operation class. Defaults to None.

        Raises:
            TypeError: If the program uses ``qp.qblox.measure_reset()``.
        """
        crosstalk_elements = CrosstalkElements(self.crosstalk)
        crosstalk_elements.flux_vector = flux_vector if flux_vector is not None else {}
        loop_idx = self.loop_depths[-1] + 1 if self.loop_depths else 0
        non_lin_flux_vector = self.non_lin_flux_vector

        non_lin_play_dict: dict[str, Waveform] = {}
        non_lin_offset_list: list[str] = []

        for i, element in enumerate(block.elements):
            if isinstance(element, MeasureReset) and not _has_named_waveform(element):
                raise TypeError("qprogram.measure_reset() cannot be used in conjunction with crosstalk compensation.")
            if (
                isinstance(element, (SetOffset, SetGain)) or _is_qblox_play(element)
            ) and element.bus in self.crosstalk.matrix:
                if non_lin_flux_vector is not None:
                    if isinstance(element, (SetOffset, SetGain)):
                        if isinstance(element, SetOffset) and element.bus in non_lin_offset_list:
                            self.non_lin_offsets.append(non_lin_flux_vector.get_corrected_offsets())
                            non_lin_offset_list = []
                        elif isinstance(element, SetOffset):
                            non_lin_offset_list.append(element.bus)
                        value = _flux_offset_value(element)
                        if isinstance(value, Variable) and value.id not in non_lin_flux_vector.variables:
                            new_loop = next(
                                loop
                                for loop in self.active_loops
                                if (_is_range_sweep(loop) and loop.variable == value)  # type: ignore[union-attr]
                                or (
                                    isinstance(loop, Parallel)
                                    and any(for_loop.variable == value for for_loop in loop.loops)
                                )
                            )
                            non_lin_flux_vector.set_loop(new_loop)
                            self.active_loops = [loop for loop in self.active_loops if loop is not new_loop]
                        non_lin_flux_vector.set_element(element)
                    else:
                        if element.bus in non_lin_play_dict:
                            self.non_lin_play_waveforms.append(
                                non_lin_flux_vector.get_corrected_play(non_lin_play_dict)
                            )
                            self.non_lin_offsets.append(non_lin_flux_vector.get_corrected_offsets())
                            non_lin_play_dict = {}
                        non_lin_offset_list.append(element.bus)
                        non_lin_play_dict[element.bus] = (
                            element.waveform if isinstance(element.waveform, Waveform) else element.waveform.get_I()  # type: ignore[union-attr]
                        )
                else:
                    crosstalk_elements.check_flux_vector(element)  # type: ignore[arg-type]
                    key = operation_key(element)  # type: ignore[arg-type]
                    crosstalk_elements.flux_vector[key] = self.handle_flux_vector(
                        flux_vector=crosstalk_elements.flux_vector[key],
                        element=element,  # type: ignore[arg-type]
                    )
                    crosstalk_elements.add_element(element, i)  # type: ignore[arg-type]
            if _passes_time(element) or (
                isinstance(element, _PLAYS)
                and not _has_named_waveform(element)
                and element.bus not in self.crosstalk.matrix
            ):
                crosstalk_elements.restart_flux_vector()

            if isinstance(element, Block):
                variable_list = None
                if _is_range_sweep(element):
                    variable_list = [element.variable]  # type: ignore[attr-defined]
                    self.active_loops.append(element)  # type: ignore[arg-type]
                    self.loop_depths.append(loop_idx)
                if isinstance(element, Parallel) and all(_is_range_sweep(loop) for loop in element.loops):
                    variable_list = [loop.variable for loop in element.loops]
                    if non_lin_flux_vector is not None:
                        self.active_loops.append(element)
                        self.loop_depths.append(loop_idx)
                    else:
                        for loop in element.loops:
                            self.active_loops.append(loop)
                            self.loop_depths.append(loop_idx)
                if non_lin_flux_vector is not None and non_lin_play_dict:
                    self.non_lin_play_waveforms.append(non_lin_flux_vector.get_corrected_play(non_lin_play_dict))
                    self.non_lin_offsets.append(non_lin_flux_vector.get_corrected_offsets())
                    non_lin_play_dict = {}
                self.traverse(element, deepcopy(crosstalk_elements.flux_vector))

                if variable_list is not None and any(variable in self.parallel_loops for variable in variable_list):
                    loop_list: list[Sweep] = []
                    for variable in (v for v in variable_list if v in self.parallel_loops):
                        valid_loops = [
                            loop
                            for loop in self.parallel_loops[variable]
                            if loop.variable in self.block_variables[variable]
                        ]
                        loop_list.extend(valid_loops)

                        for new_variable in self.block_variables[variable]:
                            self.declare(new_variable)
                        self.block_variables[variable] = []
                    block.elements[i] = self.compensated_loop_block(loop_list, element)
                    self.active_loops = self.active_loops[:-1]
                    self.loop_depths = self.loop_depths[:-1]

        if non_lin_flux_vector is None:
            self.handle_crosstalk_element(block=block, crosstalk_elements=crosstalk_elements)
        else:
            if non_lin_play_dict:
                self.non_lin_play_waveforms.append(non_lin_flux_vector.get_corrected_play(non_lin_play_dict))
                self.non_lin_offsets.append(non_lin_flux_vector.get_corrected_offsets())
                non_lin_play_dict = {}
                non_lin_offset_list = []

            if non_lin_offset_list:
                self.non_lin_offsets.append(non_lin_flux_vector.get_corrected_offsets())
                non_lin_offset_list = []

            if (
                _is_range_sweep(block)
                or (isinstance(block, Parallel) and all(_is_range_sweep(loop) for loop in block.loops))
            ) and non_lin_flux_vector.has_loop(block):  # type: ignore[arg-type]
                non_lin_flux_vector.exit_loop(block)  # type: ignore[arg-type]

    @staticmethod
    def compensated_loop_block(loops: list[Sweep], block: Block) -> Block:
        """The block replacing the user's loop ``block``: its body, run by the compensated ``loops`` in lockstep.

        Args:
            loops (list[Sweep]): The compensated loops.
            block (Block): The user's loop.

        Returns:
            Block: A ``Parallel`` of the loops, the only loop if there is one, or ``block`` itself if there is none.
        """
        if not loops:
            return block
        if len(loops) == 1:
            new_block: Block = loops[0]
        else:
            new_block = Parallel(loops)
        new_block.elements[:] = block.elements
        return new_block

    def handle_flux_vector(self, flux_vector: FluxVector, element: QbloxFluxOperation) -> FluxVector:
        """Set the flux of the element's bus in the flux vector, from its parameters, variables and loops.

        Args:
            flux_vector (FluxVector): The flux vector of the element's group.
            element (QbloxFluxOperation): The element.

        Returns:
            FluxVector: The flux vector.

        Raises:
            NotImplementedError: If the element plays an I/Q waveform.
            ValueError: If the loop sweeping the element's variable has no points.
        """
        envelope: float | Expression | np.ndarray
        if isinstance(element, SetOffset):
            envelope = element.offset_path0
        elif isinstance(element, SetGain):
            envelope = element.gain
        elif isinstance(element.waveform, Waveform):
            envelope = element.waveform.envelope()
        else:
            raise NotImplementedError(
                f"Crosstalk compensation can't play the I/Q waveform {type(element.waveform).__name__} on flux bus "
                f"{element.bus!r}."
            )

        if isinstance(envelope, Variable):
            variable_loop = next(
                (loop for loop in self.active_loops[::-1] if loop.variable == envelope),  # type: ignore[union-attr]
                None,
            )
            if variable_loop is not None:
                depth = next((d for loop, d in zip(self.active_loops, self.loop_depths) if loop is variable_loop), None)
                if depth is not None:
                    self.bus_loop_depth[element.bus] = depth
                self.variable_buses.setdefault((type(element), envelope), set()).add(element.bus)
                envelope = sweep_points(variable_loop)  # type: ignore[arg-type]
                if not envelope.tolist():
                    raise ValueError(
                        "Parameters of the ForLoop not assigned correctly. Please check start, stop and step values."
                    )
        envelope_is_array = isinstance(envelope, np.ndarray) and envelope.ndim > 0
        # The bus being set is replaced, so its previous value doesn't count.
        existing_arrays = [
            value
            for bus, value in flux_vector.flux_vector.items()
            if bus != element.bus and isinstance(value, np.ndarray) and value.ndim > 0
        ]
        ragged = (
            isinstance(element, (SetOffset, SetGain))
            and envelope_is_array
            and any(value.shape != envelope.shape for value in existing_arrays)  # type: ignore[union-attr]
        )
        if ragged:
            flux_vector.flux_vector[element.bus] = envelope  # type: ignore[assignment]
            if flux_vector.crosstalk:
                flux_vector.bias_vector[element.bus] = envelope  # type: ignore[assignment]
        else:
            flux_vector[element.bus] = envelope  # type: ignore[assignment]
        return flux_vector

    def handle_crosstalk_element(self, block: Block, crosstalk_elements: CrosstalkElements) -> Block:
        """Rewrite ``block`` for crosstalk compensation.

        Replaces each element of a group by the compensated operation on its bus, and adds the compensated operations
        on the buses the group doesn't set.

        Args:
            block (Block): The block.
            crosstalk_elements (CrosstalkElements): The groups of elements found in the block.

        Returns:
            Block: The block.
        """
        elements: dict[int, QbloxFluxOperation] = {}
        additional_elements = 0

        self.handle_crosstalk_loop(block.elements, crosstalk_elements)

        for ii, element_idx in enumerate(crosstalk_elements.element_list.keys()):
            elements[element_idx] = block.elements.pop(element_idx - ii)  # type: ignore[assignment]

        for element_idx in crosstalk_elements.element_list.keys():
            flux_vector, element_group = crosstalk_elements.element_list[element_idx]
            element = elements[element_idx]
            element_group_bus = [elements[group_id].bus for group_id in element_group]

            for bus in flux_vector.bias_vector.keys():
                if bus not in element_group_bus or element.bus == bus:
                    operation = self.handle_element(
                        element, bus, flux_vector, element_group, element_group_bus, elements
                    )
                    block.elements.insert(element_idx + additional_elements, operation)
                    if bus not in element_group_bus:
                        additional_elements += 1
        return block

    def handle_element(
        self,
        element: QbloxFluxOperation,
        bus: str,
        flux_vector: FluxVector,
        element_group: list[int],
        element_group_bus: list[str],
        elements: dict[int, QbloxFluxOperation],
    ) -> QbloxFluxOperation:
        """Build the compensated ``SetOffset``, ``SetGain`` or play of ``element`` on ``bus``.

        Args:
            element (QbloxFluxOperation): The element.
            bus (str): The bus to build the operation for.
            flux_vector (FluxVector): The flux vector of the element's group.
            element_group (list[int]): The indices of the elements of the group.
            element_group_bus (list[str]): The buses of the elements of the group.
            elements (dict[int, QbloxFluxOperation]): The elements of the block, by index.

        Returns:
            QbloxFluxOperation: The compensated operation.
        """
        bias_vector = flux_vector.bias_vector[bus]
        variable_list: list[Variable] = []
        if all(isinstance(elements[element], (SetOffset, SetGain)) for element in element_group):
            _, variable_list = self.handle_flux_v_flux(elements, flux_vector, element_group, element_group_bus)

        if isinstance(element, (SetOffset, SetGain)):
            operation, terms = self.handle_offset_or_gain(
                element,
                bus,
                bias_vector,
                element_group,
                variable_list,
                elements,  # type: ignore[arg-type]
            )
            self.flux_terms[id(operation)] = (terms, self.flux_constant(flux_vector)[bus], set(element_group_bus))
            return operation
        return self.handle_play(bus, bias_vector, element_group, elements)  # type: ignore[arg-type]

    def handle_offset_or_gain(
        self,
        element: SetOffset | SetGain,
        bus: str,
        bias_vector: float | list[float] | np.ndarray,
        element_group: list[int],
        variable_list: list[Variable],
        elements: dict[int, SetOffset | SetGain],
    ) -> tuple[SetOffset | SetGain, list[Variable]]:
        """Build the compensated ``SetOffset`` or ``SetGain`` on ``bus``, and return it with its loop terms.

        The operation only holds the loop terms. Its constant part is added by `assemble_flux_operations`.

        Args:
            element (SetOffset | SetGain): The element.
            bus (str): The bus to build the operation for.
            bias_vector (float | list[float] | np.ndarray): The compensated bias of ``bus``.
            element_group (list[int]): The indices of the elements of the group.
            variable_list (list[Variable]): The variables of the group swept by loops at different depths.
            elements (dict[int, SetOffset | SetGain]): The elements of the block, by index.

        Returns:
            tuple[SetOffset | SetGain, list[Variable]]: The operation and its loop terms.
        """
        terms: list[Variable] = []
        if isinstance(bias_vector, np.ndarray):
            value = _flux_offset_value(element)
            variable = (
                value
                if isinstance(value, Variable)
                else next(
                    (
                        _flux_offset_value(elements[element_id])
                        for element_id in element_group
                        if isinstance(_flux_offset_value(elements[element_id]), Variable)
                    ),
                    None,
                )
            )
            bus_variable = self.bus_variable_map[variable, bus]  # type: ignore[index]
            if bus_variable not in self.constant_bus_variables:
                terms.append(bus_variable)
                self.block_variables[variable].append(bus_variable)  # type: ignore[index]

            if len(variable_list) > 1 and variable in variable_list:
                for var in variable_list:
                    if isinstance(variable, Variable) and var.id != variable.id:
                        cross_variable = self.bus_variable_map[var, bus]
                        if cross_variable in self.constant_bus_variables:
                            # This loop doesn't change the bias on this bus: no term and no loop.
                            continue
                        # Only added if there are more than one loop with different variables.
                        terms.append(cross_variable)
                        self.block_variables[var].append(cross_variable)

        return type(element)(bus, terms[0] if terms else 0.0), terms

    def flux_constant(self, flux_vector: FluxVector) -> dict[str, float]:
        """The bias with every swept bus at 0: the part of the bias that doesn't change with any loop.

        That is ``M⁻¹ · (fixed flux - flux_offsets)``.

        Args:
            flux_vector (FluxVector): The flux vector.

        Returns:
            dict[str, float]: The constant bias, per bus.
        """
        fixed = {
            bus: 0.0 if isinstance(flux, np.ndarray) and flux.ndim > 0 else flux
            for bus, flux in flux_vector.flux_vector.items()
        }
        return FluxVector.from_dict(fixed).set_crosstalk(self.crosstalk)  # type: ignore[return-value]

    @staticmethod
    def handle_play(
        bus: str,
        bias_vector: float | list[float] | np.ndarray,
        element_group: list[int],
        elements: dict[int, QbloxFluxOperation],
    ) -> QbloxPlayOperation:
        """Build the compensated play on ``bus``.

        Square and FlatTop pulses stay of their type, any other pulse becomes an ``Arbitrary`` one.

        Args:
            bus (str): The bus to build the play for.
            bias_vector (float | list[float] | np.ndarray): The compensated envelope of ``bus``.
            element_group (list[int]): The indices of the plays of the group.
            elements (dict[int, QbloxFluxOperation]): The elements of the block, by index.

        Returns:
            QbloxPlayOperation: The play, a ``qp.qblox.play`` if the group's plays have a ``wait_time``.

        Raises:
            ValueError: If the plays of the group don't have the same ``wait_time``, if their FlatTop parameters
                differ, or if an ``Arbitrary`` envelope would not be an array.
        """
        play_elements = [elements[element] for element in element_group if _is_qblox_play(elements[element])]
        if len({getattr(play, "wait_time", None) for play in play_elements}) > 1:
            raise ValueError("Play elements must be the same for the same play pulse.")
        wait_time = getattr(play_elements[0], "wait_time", None)

        waveforms: Sequence[Square | FlatTop] = [elements[element].waveform for element in element_group]  # type: ignore[union-attr, misc]
        if any(isinstance(element, SetGain) for element in elements.values()):
            # Normalizes every time gain is used
            bias_vector = bias_vector / np.max(np.abs(bias_vector)) * np.sign(bias_vector)
        waveform: Waveform
        if all(isinstance(wf, Square) for wf in waveforms):
            waveform = Square(amplitude=np.max(bias_vector), duration=waveforms[0].duration)
        elif all(isinstance(wf, FlatTop) for wf in waveforms):
            if len({(wf.duration, wf.smooth_duration, wf.buffer) for wf in waveforms}) > 1:  # type: ignore[union-attr]
                raise ValueError("FlatTop parameters must be the same for all compensated pulses.")
            waveform = FlatTop(
                amplitude=np.max(np.abs(bias_vector)) * np.sign(bias_vector),
                duration=waveforms[0].duration,
                smooth_duration=waveforms[0].smooth_duration,  # type: ignore[union-attr]
                buffer=waveforms[0].buffer,  # type: ignore[union-attr]
            )
        else:
            if not isinstance(bias_vector, np.ndarray):
                raise ValueError("Arbitrary samples must be an array.")
            waveform = Arbitrary(bias_vector)

        if wait_time is None:
            return Play(bus=bus, waveform=waveform)
        return QbloxPlay(bus=bus, waveform=waveform, wait_time=wait_time)

    def handle_crosstalk_loop(
        self, elements_block: list[Block | Operation], crosstalk_elements: CrosstalkElements
    ) -> None:
        """Build the compensated loops of each variable set in the block, in ``parallel_loops``.

        They replace the user's loop of that variable once it has been traversed.

        Args:
            elements_block (list[Block | Operation]): The elements of the block.
            crosstalk_elements (CrosstalkElements): The groups of elements found in the block.
        """
        elements: dict[int, QbloxFluxOperation] = {}

        for element_idx in crosstalk_elements.element_list.keys():
            elements[element_idx] = elements_block[element_idx]  # type: ignore[assignment]

        for element_idx in crosstalk_elements.element_list.keys():
            flux_vector, element_group = crosstalk_elements.element_list[element_idx]
            element_group_bus = [elements[group_id].bus for group_id in element_group]
            element = elements[element_idx]
            variable = _element_variable(element)

            if variable is not None:
                for_loop_list = []
                list_fluxes, _ = self.handle_flux_v_flux(elements, flux_vector, element_group, element_group_bus)

                if self.flux_loops_are_nested(flux_vector) and element.bus in list_fluxes:
                    # Nested flux-vs-flux loops: use this bus's per-variable decomposition so each
                    # loop level contributes only its own crosstalk term; the other levels are
                    # carried in later by assemble_flux_operations.
                    source = list_fluxes[element.bus]
                else:
                    # Lockstep (parallel/single) loops: use the combined compensated bias.
                    source = flux_vector
                # The compensated loops sweep only the part of the bias that changes with the loop. The constant
                # part is added once per operation by assemble_flux_operations.
                constant = self.flux_constant(source)
                for bus in self.crosstalk.matrix.keys():
                    loop = self.make_for_loop(variable, bus, source.bias_vector[bus] - constant[bus])  # type: ignore[arg-type, operator]
                    if loop is not None:
                        for_loop_list.append(loop)

                self.parallel_loops[variable] = for_loop_list

                if variable not in self.block_variables:
                    self.block_variables[variable] = []

    def handle_flux_v_flux(
        self,
        elements: dict[int, QbloxFluxOperation],
        flux_vector: FluxVector,
        element_group: list[int],
        element_group_bus: list[str],
    ) -> tuple[dict[str, FluxVector], list[Variable]]:
        """Decompose the flux vector into one flux vector per loop that sets a variable of the group.

        This is for loops executed one inside the other, such as flux vs flux.

        Args:
            elements (dict[int, QbloxFluxOperation]): The elements of the block, by index.
            flux_vector (FluxVector): The flux vector of the group.
            element_group (list[int]): The indices of the elements of the group.
            element_group_bus (list[str]): The buses of the elements of the group.

        Returns:
            tuple[dict[str, FluxVector], list[Variable]]: The flux vector of each bus set by a loop variable, and those
            variables, one per loop depth.
        """
        bus_list = []
        variable_list = []
        used_loop_indices = set()
        for ii, element_idx in enumerate(element_group):
            element = elements[element_idx]
            variable = _element_variable(element)
            if variable is not None and variable in [loop.variable for loop in self.active_loops]:  # type: ignore[union-attr]
                loop_idx = next(
                    (idx for loop, idx in zip(self.active_loops, self.loop_depths) if loop.variable == variable),  # type: ignore[union-attr]
                    None,
                )
                if loop_idx is not None and loop_idx not in used_loop_indices:
                    used_loop_indices.add(loop_idx)
                    bus_list.append(element_group_bus[ii])
                    variable_list.append(variable)
        if self.flux_loops_are_nested(flux_vector):
            reduced = FluxVector.from_dict(
                {bus: (flux if bus in bus_list else 0) for bus, flux in flux_vector.flux_vector.items()}
            )
            reduced.crosstalk = flux_vector.crosstalk
            return reduced.get_decomposed_vector(bus_list), variable_list
        return flux_vector.get_decomposed_vector(bus_list), variable_list

    def flux_loops_are_nested(self, flux_vector: FluxVector) -> bool:
        """Whether the swept flux buses are swept by loops at different depths.

        That is a flux-vs-flux sweep across levels, as opposed to a single lockstep parallel or loop.

        Args:
            flux_vector (FluxVector): The flux vector.

        Returns:
            bool: True if the swept buses are swept at more than one depth.
        """
        depths = {
            self.bus_loop_depth.get(bus)
            for bus, flux in flux_vector.flux_vector.items()
            if isinstance(flux, np.ndarray) and flux.ndim > 0
        }
        depths.discard(None)
        return len(depths) > 1

    def make_for_loop(self, variable: Variable, bus: str, bias_vector: Sequence[float]) -> Sweep | None:
        """Build the compensated loop of ``variable`` on ``bus``, sweeping ``bias_vector``.

        Args:
            variable (Variable): The user's loop variable.
            bus (str): The bus.
            bias_vector (Sequence[float]): The compensated bias of ``bus`` at each point of the loop.

        Returns:
            Sweep | None: The loop, or None if the loop doesn't change the bias on ``bus``.

        Raises:
            NotImplementedError: If the loop has a single point.
        """
        if len(bias_vector) < 2:
            raise NotImplementedError("Single point loops are not supported.")
        if (variable, bus) not in self.bus_variable_map:
            self.bus_variable_map[variable, bus] = self.new_variable(f"{bus}_{variable.id}")
        bus_variable = self.bus_variable_map[variable, bus]

        start, stop = bias_vector[0], bias_vector[-1]
        step = bias_vector[1] - bias_vector[0]

        if abs(step) < 1e-12:
            # This loop doesn't change the bias on this bus: no compensated loop and no term.
            self.constant_bus_variables.add(bus_variable)
            return None

        return Sweep(bus_variable, ForLoop(bus_variable, start, stop, step).to_range())

    def assemble_flux_operations(
        self,
        block: Block,
        carried: dict[tuple[type, str], list[Variable]],
        ancestors: list[Block],
        shifted_loops: dict[tuple[Variable, float], Variable],
    ) -> None:
        """Set the final value of every compensated ``SetOffset`` and ``SetGain``.

        That is its own loop terms, plus the loop terms of enclosing blocks that are still active, plus its constant
        bias. Operations are followed in program order, as the hardware runs them. A loop's terms stop being carried
        once the buses it sweeps are set again, so a later operation replaces an earlier one. Constants are never
        carried: each operation's constant already includes every fixed flux set before it.

        Args:
            block (Block): The block.
            carried (dict[tuple[type, str], list[Variable]]): The loop terms active on entering the block, per operation
                class and bus.
            ancestors (list[Block]): The blocks enclosing ``block``, outermost first.
            shifted_loops (dict[tuple[Variable, float], Variable]): The shifted copies of compensated loops created so
                far, by loop variable and shift.

        Raises:
            NotImplementedError: If an inner block sets only some of the buses an outer loop sweeps together.
        """
        ancestors = [*ancestors, block]
        current = {key: list(terms) for key, terms in carried.items()}
        # (operation class, loop variable) whose buses have been set again in this block.
        replaced: set[tuple[type, Variable]] = set()
        for element in block.elements:
            if isinstance(element, Block):
                active = {
                    (cls, bus): [term for term in terms if (cls, self.bus_variable_origin[term]) not in replaced]
                    for (cls, bus), terms in current.items()
                }
                self.assemble_flux_operations(element, active, ancestors, shifted_loops)
                continue
            if not isinstance(element, (SetOffset, SetGain)) or id(element) not in self.flux_terms:
                continue

            own_terms, constant, group_buses = self.flux_terms.pop(id(element))
            operation_class = type(element)
            for (cls, _), terms in carried.items():
                if cls is not operation_class:
                    continue
                for term in terms:
                    variable = self.bus_variable_origin[term]
                    swept = self.variable_buses.get((operation_class, variable), set())
                    reset = swept & group_buses
                    if swept and reset == swept:
                        replaced.add((operation_class, variable))
                    elif reset:
                        raise NotImplementedError(
                            f"Crosstalk compensation can't set only some of the buses an outer loop sweeps "
                            f"together: loop variable {variable.id!r} sweeps {sorted(swept)}, and an inner "
                            f"block sets {sorted(reset)} again. Set all of them in the inner block, or none."
                        )

            key = (operation_class, element.bus)
            inherited = [
                term
                for term in carried.get(key, [])
                if (operation_class, self.bus_variable_origin[term]) not in replaced and term not in own_terms
            ]
            terms = own_terms + inherited
            _set_flux_offset_value(element, self.combine_terms(terms, constant, ancestors, shifted_loops))
            current[key] = terms

    def combine_terms(
        self,
        terms: list[Variable],
        constant: float,
        ancestors: list[Block],
        shifted_loops: dict[tuple[Variable, float], Variable],
    ) -> float | Expression:
        """Write ``sum(terms) + constant`` as a value the Qblox compiler accepts.

        The compiler takes a single binary operation, so ``var + var + constant`` is written as ``var + shifted_var``,
        where ``shifted_var`` is a copy of the innermost compensated loop with its range moved by the constant.

        Args:
            terms (list[Variable]): The loop terms.
            constant (float): The constant bias.
            ancestors (list[Block]): The blocks enclosing the operation, outermost first.
            shifted_loops (dict[tuple[Variable, float], Variable]): The shifted copies of compensated loops created so
                far, by loop variable and shift.

        Returns:
            float | Expression: The value.

        Raises:
            NotImplementedError: If more than two loops sweep the flux at the same time.
        """
        constant = float(constant) if abs(constant) >= 1e-12 else 0.0
        if not terms:
            return constant
        if len(terms) > 2:
            raise NotImplementedError(
                "Crosstalk compensation supports at most two loops sweeping flux at the same time on one bus."
            )
        if len(terms) == 1:
            return terms[0] + constant if constant else terms[0]
        if not constant:
            return terms[0] + terms[1]

        parallel, loop = next(
            (block, loop) for block in reversed(ancestors) for loop in _header_loops(block) if loop.variable in terms
        )
        other = next(term for term in terms if term != loop.variable)
        key = (loop.variable, round(constant, 12))
        if key not in shifted_loops:
            source = loop.source
            shifted = self.new_variable(f"{loop.variable.id}{_shift_suffix(constant)}")
            shifted_loop = Sweep(
                shifted,
                ForLoop(shifted, source.start + constant, source.stop + constant, source.step).to_range(),  # type: ignore[attr-defined]
            )
            if isinstance(parallel, Parallel):
                parallel.loops = [*parallel.loops, shifted_loop]
            else:
                # A compensated loop alone in its block: it becomes a Parallel once every operation is assembled.
                self.extra_loops.setdefault(id(parallel), (parallel, []))[1].append(shifted_loop)  # type: ignore[arg-type]
            self.declare(shifted)
            shifted_loops[key] = shifted
        return other + shifted_loops[key]

    def attach_extra_loops(self, block: Block) -> None:
        """Turn each compensated loop that got shifted copies into a ``Parallel`` running them in lockstep.

        Args:
            block (Block): The block whose descendants to rewrite.
        """
        for index, element in enumerate(block.elements):
            if not isinstance(element, Block):
                continue
            self.attach_extra_loops(element)
            if id(element) in self.extra_loops:
                loop, extra = self.extra_loops[id(element)]
                parallel = Parallel([Sweep(loop.variable, loop.source), *extra])
                parallel.elements[:] = loop.elements
                block.elements[index] = parallel

    def handle_non_linear(
        self,
        elements: list[Block | Operation],
        flux_vector: NonLinearFluxVector,
        offsets: list[dict[str, np.ndarray]],
        play_waveforms: list[dict[str, np.ndarray]],
        loop_index: tuple[int, ...] = (),
        loop_coord: tuple[int, ...] = (0,),
        state: NonLinearFlagState | None = None,
    ) -> tuple[list[Block | Operation], NonLinearFlagState]:
        """Rewrite the elements for a non-linear crosstalk compensation.

        - Unpacks the gain and offset loops involving flux buses.
        - Calculates the non-linear offsets and the non-linear waveforms.
        - Removes the ``set_gain``, folded into the play envelopes.
        - Makes Square pulses more efficient by keeping the same envelope and changing its gain.
        - Handles offsets and waveforms across all possible combinations of loops.

        Args:
            elements (list[Block | Operation]): The elements of the block.
            flux_vector (NonLinearFluxVector): The non-linear flux vector.
            offsets (list[dict[str, np.ndarray]]): The non-linear offsets, in order of creation.
            play_waveforms (list[dict[str, np.ndarray]]): The non-linear waveforms, in order of creation.
            loop_index (tuple[int, ...], optional): Index of the current point of each unrolled loop. Defaults to ().
            loop_coord (tuple[int, ...], optional): Coordinates of the waveform or offset in the non-linear matrices.
                Defaults to (0,).
            state (NonLinearFlagState | None, optional): The cursors over ``offsets`` and ``play_waveforms``. Defaults
                to a new one.

        Returns:
            tuple[list[Block | Operation], NonLinearFlagState]: The rewritten elements, and the cursors after them.
        """
        state = state if state is not None else NonLinearFlagState()
        corrected_elements: list[Block | Operation] = []
        flux_vector_buses = sorted(flux_vector.buses)

        for element in elements:
            if isinstance(element, SetGain) and element.bus in flux_vector_buses:
                continue

            if isinstance(element, SetOffset) and element.bus in flux_vector_buses:
                if state.offsets_index != state.last_appended_offset:
                    state.on_offset()
                    for bus in flux_vector_buses:
                        corrected_offsets = offsets[state.offsets_index][bus][loop_coord]
                        corrected_elements.append(SetOffset(bus, corrected_offsets))

            elif _is_qblox_play(element) and element.bus in flux_vector_buses:  # type: ignore[union-attr]
                if not state.play_bus_list or element.bus in state.play_bus_list:  # type: ignore[union-attr]
                    for bus in flux_vector_buses:
                        corrected_waveform = play_waveforms[state.plays_index][bus][loop_coord]
                        if isinstance(corrected_waveform, Square):
                            corrected_elements.append(SetGain(bus, corrected_waveform.amplitude))
                            corrected_waveform = Square(amplitude=1, duration=corrected_waveform.duration)
                        else:
                            corrected_elements.append(SetGain(bus, 1))
                        if not state.offset_defined:
                            corrected_offsets = offsets[state.offsets_index][bus][loop_coord]
                            corrected_elements.append(SetOffset(bus, corrected_offsets))
                        if isinstance(element, QbloxPlay):
                            corrected_elements.append(QbloxPlay(bus, corrected_waveform, element.wait_time))
                        else:
                            corrected_elements.append(Play(bus, corrected_waveform))
                    state.on_play(element.bus)  # type: ignore[union-attr]

            elif isinstance(element, Wait) and element.bus in flux_vector_buses:
                corrected_elements.append(element)
                state.on_wait()

            elif isinstance(element, Block):
                state.on_block()
                if flux_vector.has_loop(element):
                    shape = next(iter(offsets[state.offsets_index].values())).shape
                    offsets_index = state.offsets_index
                    plays_index = state.plays_index
                    for key in range(shape[-len(loop_index) - 1]):
                        loop_coord = (key, *loop_index[::-1])
                        corrected_loop, state = self.handle_non_linear(
                            elements=element.elements,
                            flux_vector=flux_vector,
                            offsets=offsets,
                            play_waveforms=play_waveforms,
                            loop_index=(*loop_index, key),
                            loop_coord=loop_coord,
                            state=NonLinearFlagState(offsets_index=offsets_index, plays_index=plays_index),
                        )
                        corrected_elements.extend(corrected_loop)
                    loop_coord = loop_coord[:-1]
                    if not loop_coord:
                        loop_coord = (0,)
                else:
                    corrected_loop, state = self.handle_non_linear(
                        elements=element.elements,
                        flux_vector=flux_vector,
                        offsets=offsets,
                        play_waveforms=play_waveforms,
                        loop_index=loop_index,
                        loop_coord=loop_coord,
                        state=NonLinearFlagState(offsets_index=state.offsets_index, plays_index=state.plays_index),
                    )
                    element_copy = deepcopy(element)
                    element_copy.elements[:] = corrected_loop
                    corrected_elements.append(element_copy)
                state.after_block()
            else:
                corrected_elements.append(element)

        # Needs to sync at the end of every loop for the unpack to work with non-flux buses.
        # Skipped when the tail ends in an IfTrigger (possibly wrapped in loops): a qp.if_trigger() block already
        # self-times its own exit (see QbloxCompiler._handle_conditional_trigger_epilogue), and appending a Sync right
        # after it would touch the conditional's gated bus outside the block, which the Qblox pre-pass
        # (qililab.qprogram.prepass.qblox_prepass) forbids.
        if (
            corrected_elements
            and not isinstance(corrected_elements[-1], Sync)
            and not _ends_in_if_trigger(corrected_elements[-1])
        ):
            corrected_elements.append(Sync())
        return corrected_elements, state


def apply_crosstalk_qblox(qprogram: QProgram, crosstalk: CrosstalkMatrix) -> QProgram:
    """Apply crosstalk compensation to the Qblox flux operations of a QProgram.

    Traverses the elements of the QProgram, replacing every ``play`` (``qp.play`` or ``qp.qblox.play``),
    ``set_offset`` and ``set_gain`` on a bus of the crosstalk matrix by the compensated operations on all the buses of
    the matrix.

    Args:
        qprogram (QProgram): The QProgram. It is not modified.
        crosstalk (CrosstalkMatrix): Crosstalk matrix class.

    Returns:
        QProgram: A new instance of QProgram with calibrated crosstalk.

    Raises:
        TypeError: If the QProgram uses ``qp.qblox.measure_reset()``.
        NotImplementedError: If a loop sweeping flux has a single point, if more than two loops sweep flux on one bus
            at the same time, or if an inner block sets only some of the buses an outer loop sweeps together.
        ValueError: If the plays compensated together have different ``wait_time`` or FlatTop parameters.
    """
    copied_qprogram = deepcopy(qprogram)
    _QbloxCrosstalkCompensation(copied_qprogram, crosstalk).run()
    return copied_qprogram


def apply_crosstalk_qdac(
    qprogram: QProgram,
    crosstalk: CrosstalkMatrix,
    qdac_buses_offset: dict[str, float],
    target_fluxes: dict[str, float | list[float] | np.ndarray] | None = None,
) -> QProgram:
    """Apply crosstalk compensation to the QDAC flux operations of a QProgram.

    Traverses the elements of the QProgram, replacing every ``qp.qdac.play`` and ``qp.qdac.set_offset`` on a bus of the
    crosstalk matrix by the compensated operations on all the buses of the matrix.

    Args:
        qprogram (QProgram): The QProgram. It is not modified.
        crosstalk (CrosstalkMatrix): Crosstalk matrix class.
        qdac_buses_offset (dict[str, float]): Hardware bias voltage per bus, used to recover the parked flux only
            when ``target_fluxes`` is not provided.
        target_fluxes (dict[str, float | list[float] | np.ndarray] | None, optional): Target flux per bus for the
            parked operating point. Defaults to None.

    Returns:
        QProgram: A new instance of QProgram with calibrated crosstalk.

    Raises:
        ValueError: If the plays compensated together have envelopes of different sizes.
    """

    def traverse(block: Block, flux_vector: FluxVector | None = None) -> None:
        """Compensate the QDAC flux operations of ``block`` and, first, of its nested blocks.

        Args:
            block (Block): The block.
            flux_vector (FluxVector | None, optional): The flux vector so far. Defaults to the parked flux.
        """
        element_list = []

        if flux_vector is None:
            flux_vector = FluxVector()
            if target_fluxes:
                flux_vector.set_crosstalk(crosstalk)
                flux_vector.flux_vector.update(
                    {bus: target_fluxes[bus] for bus in crosstalk.matrix if bus in target_fluxes}
                )
            else:
                # Fallback: no tracked target flux -> recover it from the hardware bias voltage.
                flux_vector.set_crosstalk_from_bias(crosstalk, qdac_buses_offset)  # type: ignore[arg-type]

        for i, element in enumerate(block.elements):
            if (
                isinstance(element, (QdacPlay, QdacSetOffset))
                and not _has_named_waveform(element)
                and element.bus in crosstalk.matrix
            ):
                element_list.append(i)
                flux_vector = handle_flux_vector(flux_vector=flux_vector, element=element)

            if isinstance(element, Block):
                traverse(element, flux_vector)

        handle_crosstalk_element(block=block, element_list=element_list, flux_vector=flux_vector)

    def handle_flux_vector(flux_vector: FluxVector, element: QdacPlay | QdacSetOffset) -> FluxVector:
        """Set the flux of the element's bus in the flux vector.

        Args:
            flux_vector (FluxVector): The flux vector.
            element (QdacPlay | QdacSetOffset): The element.

        Returns:
            FluxVector: The flux vector.

        Raises:
            ValueError: If the element plays an envelope of another size than the ones already in the flux vector.
        """
        envelope: float | Expression | np.ndarray
        if isinstance(element, QdacSetOffset):
            envelope = element.offset
        elif isinstance(element.waveform, Waveform):
            envelope = element.waveform.envelope()
        elif isinstance(element.waveform, IQWaveform):
            envelope = element.waveform.get_I().envelope()

        if isinstance(envelope, np.ndarray):
            existing_lengths = {
                len(flux_v) for flux_v in flux_vector.flux_vector.values() if isinstance(flux_v, (np.ndarray, list))
            }
            if existing_lengths and envelope.shape[0] not in existing_lengths:
                raise ValueError("QProgram.play elements must have the same size.")
        flux_vector.flux_vector[element.bus] = envelope  # type: ignore[assignment]
        return flux_vector

    def handle_crosstalk_element(block: Block, element_list: list[int], flux_vector: FluxVector) -> None:
        """Replace the QDAC flux operations of ``block`` by the compensated ones on every bus of the matrix.

        Args:
            block (Block): The block.
            element_list (list[int]): The indices of its QDAC flux operations.
            flux_vector (FluxVector): The flux vector.
        """
        flux_vector.update_bias_vector()
        if element_list:
            elements = []
            for ii, element_idx in enumerate(element_list):
                elements.append(block.elements.pop(element_idx - ii))

            play_elements = [element for element in elements if isinstance(element, QdacPlay)]
            if play_elements:
                dwell, delay, repetitions, stepped = (
                    play_elements[0].dwell,
                    play_elements[0].delay,
                    play_elements[0].repetitions,
                    play_elements[0].stepped,
                )

            for bus in flux_vector.bias_vector.keys():
                if isinstance(flux_vector.bias_vector[bus], float):
                    offset = QdacSetOffset(bus, flux_vector.bias_vector[bus])  # type: ignore[arg-type]
                    block.elements.insert(element_list[0], offset)
                elif isinstance(flux_vector.bias_vector[bus], (np.ndarray, list)) and play_elements:
                    play = QdacPlay(
                        bus,
                        Arbitrary(flux_vector.bias_vector[bus]),  # type: ignore[arg-type]
                        dwell=dwell,
                        delay=delay,
                        repetitions=repetitions,
                        stepped=stepped,
                    )
                    block.elements.insert(element_list[0], play)

    copied_qprogram = deepcopy(qprogram)
    traverse(copied_qprogram.body)
    return copied_qprogram
