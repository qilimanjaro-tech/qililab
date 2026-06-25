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

"""Flux-crosstalk *compensation lowering* for the new ``qprogram`` AST.

This module is the new-AST port of the legacy ``QProgram.with_crosstalk_qblox`` /
``QProgram.with_crosstalk_qdac`` methods. It is a **static, deep-copying AST transform**: given a
program that contains a ``program.qililab.set_crosstalk(matrix)`` op and flux operations, it returns
a *new* program whose flux operations are replaced/augmented by the crosstalk-compensated values, so
the rest of the pipeline (validation, partition, QDAC + Qblox compilation) sees only plain,
already-compensated flux ops and needs no crosstalk awareness.

The compensation math is **not** re-implemented here — it lives in
:class:`~qililab.qprogram.crosstalk_matrix.CrosstalkMatrix` /
:class:`~qililab.qprogram.crosstalk_matrix.NonLinearCrosstalkMatrix` and
:class:`~qililab.qprogram.flux_vector.FluxVector` /
:class:`~qililab.qprogram.flux_vector.NonLinearFluxVector`, exactly as in the legacy stack. Those
classes were written against the *legacy* AST (legacy ``Variable`` / ``ForLoop`` types), so this
module bridges the two: it walks the new AST and drives the same math objects, converting new-AST
:class:`~qprogram.variable.Variable` references to the legacy ``Variable`` shape the math expects.

Two flux *families* are handled, mirroring the two legacy methods:

* **qblox flux** — flux ops are the *core* ops :class:`~qprogram.operations.SetOffset` /
  :class:`~qprogram.operations.SetGain` / :class:`~qprogram.operations.Play`. Compensation runs
  through ``flux_to_bias`` (linear) or the :class:`NonLinearFluxVector` collection (non-linear), and
  the compensated ops are inserted as the same core op types.
* **qdac flux** — flux ops are the *vendor* ops :class:`qprogram_qdac.operations.SetOffset` /
  :class:`qprogram_qdac.operations.Play`. Compensation runs through ``set_crosstalk_from_bias``
  (mirroring legacy ``with_crosstalk_qdac``) and the compensated ops are inserted as the same vendor
  op types.

The family is detected per program from the flux op types actually present; a program may not mix
the two on crosstalk buses.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import numpy as np
from qprogram.blocks import Block, ForLoop, Loop, Parallel
from qprogram.operations import Measure, Play, SetGain, SetOffset, Sync, Wait
from qprogram.variable import BinaryOp, Constant, Expression, Variable
from qprogram.waveforms import Arbitrary, IQWaveform, Square, Waveform

from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, NonLinearCrosstalkMatrix
from qililab.qprogram.flux_vector import FluxVector, NonLinearFluxVector
from qililab.qprogram.v2.vendor import SetCrosstalk

try:  # qdac vendor ops (flux family); optional at import time
    from qprogram_qdac.operations import Play as QdacPlay
    from qprogram_qdac.operations import SetOffset as QdacSetOffset

    _QDAC_FLUX_OPS: tuple[type, ...] = (QdacSetOffset, QdacPlay)
except ImportError:  # pragma: no cover - qdac extension not installed
    QdacPlay = None  # type: ignore[assignment,misc]
    QdacSetOffset = None  # type: ignore[assignment,misc]
    _QDAC_FLUX_OPS = ()

if TYPE_CHECKING:
    from qprogram.qprogram import QProgram

#: Core flux op types (qblox-driven flux). ``SetGain`` only ever appears in the qblox family.
_CORE_FLUX_OPS: tuple[type, ...] = (SetOffset, SetGain, Play)


# --------------------------------------------------------------------------- public API


def extract_crosstalk(qprogram: QProgram) -> CrosstalkMatrix | None:
    """Return the crosstalk matrix carried by the program's ``set_crosstalk`` op, or ``None``.

    Walks the whole program (including block bodies / conditional arms) for a
    :class:`~qililab.qprogram.v2.vendor.SetCrosstalk` op and returns the (last) matrix installed.

    Args:
        qprogram: The program to inspect.

    Returns:
        The :class:`~qililab.qprogram.crosstalk_matrix.CrosstalkMatrix` (or
        :class:`NonLinearCrosstalkMatrix`) from the program's ``set_crosstalk`` op, or ``None`` if the
        program has no such op.
    """
    matrix: CrosstalkMatrix | None = None
    for node in qprogram.body.walk():
        if isinstance(node, SetCrosstalk):
            matrix = node.crosstalk
    return matrix


def apply_crosstalk_compensation(qprogram: QProgram, crosstalk: CrosstalkMatrix) -> QProgram:
    """Lower flux-crosstalk compensation into a copy of ``qprogram``.

    Deep-copies ``qprogram`` and replaces / injects compensated flux operations on every bus named in
    ``crosstalk.matrix`` so the resulting program drives the hardware bias values that realise the
    requested target fluxes. The transform is static (no execution): it does the same math the legacy
    ``with_crosstalk_qblox`` / ``with_crosstalk_qdac`` did, reusing the same
    :class:`CrosstalkMatrix` / :class:`FluxVector` machinery.

    Linear (:class:`CrosstalkMatrix`) and non-linear (:class:`NonLinearCrosstalkMatrix`) matrices are
    both supported; the flux family (core qblox ops vs ``qprogram_qdac`` vendor ops) is auto-detected.

    Args:
        qprogram: The program to compensate (typically already ``expand()``-ed).
        crosstalk: The crosstalk matrix to compensate against.

    Returns:
        A new :class:`~qprogram.QProgram` with compensated flux operations. The input is left
        unchanged.

    Raises:
        TypeError: If the program uses ``qblox.active_reset`` together with crosstalk compensation
            (incompatible, mirroring the legacy ``measure_reset`` restriction).
        ValueError: If both the core-op and qdac vendor-op flux families touch crosstalk buses, or on
            the same shape/parameter conflicts the legacy lowering rejected.
    """
    copied = deepcopy(qprogram)
    _reject_active_reset(copied)
    # The ``set_crosstalk`` op has done its job (the matrix is consumed here, and recorded on the
    # platform by the executor); drop it so the lowered program is a plain flux program.
    _strip_set_crosstalk(copied)

    family = _detect_flux_family(copied, crosstalk)
    if family is None:
        # No flux ops on any crosstalk bus — nothing to compensate.
        return copied

    if family == "qdac":
        _QdacLinearLowering(crosstalk).run(copied)
        return copied

    # qblox (core ops): linear or non-linear.
    if isinstance(crosstalk, NonLinearCrosstalkMatrix):
        _QbloxNonLinearLowering(crosstalk).run(copied)
    else:
        _QbloxLinearLowering(crosstalk).run(copied)
    return copied


# --------------------------------------------------------------------------- shared helpers


def _reject_active_reset(qprogram: QProgram) -> None:
    """Raise if the program uses ``qblox.active_reset`` (incompatible with crosstalk compensation)."""
    try:
        from qprogram_qblox.operations import ActiveReset
    except ImportError:  # pragma: no cover - qblox extension not installed
        return
    for node in qprogram.body.walk():
        if isinstance(node, ActiveReset):
            raise TypeError(
                "qblox.active_reset cannot be used in conjunction with crosstalk compensation."
            )


def _strip_set_crosstalk(qprogram: QProgram) -> None:
    """Remove every :class:`SetCrosstalk` op from the program (in every block)."""

    def strip(block: Block) -> None:
        block._elements = [el for el in block._elements if not isinstance(el, SetCrosstalk)]
        for el in block._elements:
            if isinstance(el, Block):
                strip(el)

    strip(qprogram.body)


def _detect_flux_family(qprogram: QProgram, crosstalk: CrosstalkMatrix) -> str | None:
    """Return ``"qblox"`` / ``"qdac"`` / ``None`` for the flux family touching crosstalk buses."""
    buses = set(crosstalk.matrix.keys())
    has_core = False
    has_qdac = False
    for node in qprogram.body.walk():
        if getattr(node, "bus", None) not in buses:
            continue
        if _QDAC_FLUX_OPS and isinstance(node, _QDAC_FLUX_OPS):
            has_qdac = True
        elif isinstance(node, _CORE_FLUX_OPS):
            has_core = True
    if has_core and has_qdac:
        raise ValueError(
            "Crosstalk compensation cannot mix core (qblox) flux ops and qdac vendor flux ops on the "
            "same crosstalk buses."
        )
    if has_qdac:
        return "qdac"
    if has_core:
        return "qblox"
    return None


def _to_legacy_expression(expr: object):
    """Convert a new-AST :class:`~qprogram.variable.Variable` / :class:`BinaryOp` to the legacy shape.

    The :class:`FluxVector` math objects key on a legacy ``Variable.label``; the new AST uses
    ``Variable.id``. This returns a legacy ``Variable`` / ``VariableExpression`` (with matching
    ``label``\\ s) for symbolic values, or a plain ``float`` for concrete ones.
    """
    from qililab.core.variables import Variable as LegacyVariable
    from qililab.core.variables import VariableExpression as LegacyVariableExpression

    if isinstance(expr, Variable):
        return LegacyVariable(label=expr.id)
    if isinstance(expr, BinaryOp):
        op = getattr(expr, "op", "+")
        operator = op if op in ("+", "-") else "+"
        return LegacyVariableExpression(_to_legacy_expression(expr.left), operator, _to_legacy_expression(expr.right))
    if isinstance(expr, Constant):
        return float(expr.value)
    if isinstance(expr, Expression):
        # An expression shape the legacy math cannot represent (e.g. a product). Resolve to a number
        # if it is already concrete; otherwise fall through and let the math object reject it.
        return float(expr.evaluate_or_raise())
    return float(expr)


def _loop_values(loop: ForLoop | Loop) -> np.ndarray:
    """Sweep values of a new-AST loop block (inclusive ``ForLoop``)."""
    if isinstance(loop, ForLoop):
        return loop.start + loop.step * np.arange(loop.num_iterations())
    return np.asarray(loop.values)


def _single_waveform(waveform: object) -> Waveform:
    """Return the single-path waveform driving a flux ``Play`` (I component for an IQ waveform)."""
    if isinstance(waveform, IQWaveform):
        return waveform.get_I()
    return waveform  # type: ignore[return-value]


# --------------------------------------------------------------------------- qblox linear lowering


class _QbloxLinearLowering:
    """Linear crosstalk lowering for the core (qblox) flux family.

    Walks each block and groups consecutive flux ops (until a ``Wait`` / ``Measure`` / non-flux
    ``Play`` breaks the run, mirroring the legacy ``restart_flux_vector`` triggers). For each group it
    computes the per-bus hardware bias via :meth:`CrosstalkMatrix.flux_to_bias` and replaces the
    group with one compensated op per crosstalk bus.

    Swept (variable) flux values are realised by computing the compensated bias over the enclosing
    sweep's values and emitting an :class:`~qprogram.waveforms.Arbitrary` ``Play`` (the static analogue
    of the legacy parallel-loop variable rewrite — it produces the identical per-iteration bias values
    without needing a synthesized parallel loop, since the executor unrolls software sweeps anyway).
    """

    def __init__(self, crosstalk: CrosstalkMatrix) -> None:
        self._crosstalk = crosstalk
        self._buses = list(crosstalk.matrix.keys())

    def run(self, qprogram: QProgram) -> None:
        self._traverse(qprogram.body, active_loops=[])

    def _traverse(self, block: Block, active_loops: list[ForLoop | Parallel]) -> None:
        # First recurse into child blocks (with the loop stack extended), then compensate this block's
        # own immediate flux ops. Post-order keeps inner blocks already-lowered when we rewrite here.
        for element in block.elements:
            if isinstance(element, Block):
                child_loops = active_loops
                if isinstance(element, (ForLoop, Parallel)):
                    child_loops = [*active_loops, element]
                self._traverse(element, child_loops)
        self._compensate_block(block, active_loops)

    def _compensate_block(self, block: Block, active_loops: list[ForLoop | Parallel]) -> None:
        # Identify maximal runs of flux ops on crosstalk buses, split by run-breaking ops.
        groups = self._collect_groups(block)
        # Rewrite right-to-left so earlier indices stay valid.
        for start, ops in reversed(groups):
            replacement = self._compensate_group(ops, active_loops)
            block._elements[start : start + len(ops)] = replacement

    def _collect_groups(self, block: Block) -> list[tuple[int, list]]:
        groups: list[tuple[int, list]] = []
        current: list = []
        current_start = 0
        for i, element in enumerate(block.elements):
            is_flux = isinstance(element, _CORE_FLUX_OPS) and element.bus in self._buses
            breaks_run = isinstance(element, (Wait, Measure)) or (
                isinstance(element, Play) and element.bus not in self._buses
            )
            if is_flux:
                if not current:
                    current_start = i
                current.append(element)
            elif breaks_run or isinstance(element, Block):
                if current:
                    groups.append((current_start, current))
                    current = []
        if current:
            groups.append((current_start, current))
        return groups

    def _compensate_group(self, ops: list, active_loops: list[ForLoop | Parallel]) -> list:
        # Build the target-flux dict for this group: one entry per touched bus.
        flux: dict[str, float | np.ndarray] = {}
        kind: dict[str, type] = {}
        play_template: Play | None = None
        for op in ops:
            if isinstance(op, SetOffset):
                flux[op.bus] = self._scalar_or_sweep(op.offset_path0, active_loops)
                kind[op.bus] = SetOffset
            elif isinstance(op, SetGain):
                flux[op.bus] = self._scalar_or_sweep(op.gain, active_loops)
                kind[op.bus] = SetGain
            elif isinstance(op, Play):
                flux[op.bus] = _single_waveform(op.waveform).envelope()
                kind[op.bus] = Play
                play_template = op

        # Buses absent from the group default to zero target flux (legacy behaviour).
        for bus in self._buses:
            flux.setdefault(bus, 0.0)

        bias = self._crosstalk.flux_to_bias(flux)

        replacement: list = []
        for bus in self._buses:
            op_kind = kind.get(bus)
            value = bias[bus]
            if op_kind is Play or (op_kind is None and isinstance(value, np.ndarray)):
                replacement.append(self._make_play(bus, value, play_template))
            elif op_kind is SetGain:
                replacement.append(SetGain(bus, self._as_value(value)))
            else:  # SetOffset, or an absent bus alongside scalar targets
                replacement.append(SetOffset(bus, self._as_value(value)))
        return replacement

    def _scalar_or_sweep(self, value: object, active_loops: list[ForLoop | Parallel]) -> float | np.ndarray:
        """Resolve a flux value to a scalar or, for a swept variable, the array of its loop values."""
        if isinstance(value, Variable):
            for loop in reversed(active_loops):
                if isinstance(loop, ForLoop) and loop.variable.id == value.id:
                    return _loop_values(loop)
                if isinstance(loop, Parallel):
                    for inner in loop.loops:
                        if inner.variable.id == value.id:
                            return _loop_values(inner)
            # Bound elsewhere / concrete — evaluate.
            return float(value.evaluate_or_raise())
        if isinstance(value, Expression):
            return float(value.evaluate_or_raise())
        return float(value)

    @staticmethod
    def _as_value(value: float | np.ndarray) -> float:
        if isinstance(value, np.ndarray):
            return float(value.reshape(-1)[0])
        return float(value)

    @staticmethod
    def _make_play(bus: str, value: float | np.ndarray, template: Play | None) -> Play:
        samples = value if isinstance(value, np.ndarray) else np.asarray([value])
        return Play(bus=bus, waveform=Arbitrary(samples))


# --------------------------------------------------------------------------- qblox non-linear lowering


class _QbloxNonLinearLowering:
    """Non-linear crosstalk lowering for the core (qblox) flux family.

    A faithful port of the legacy ``with_crosstalk_qblox`` non-linear branch: a first *collection*
    pass walks the AST and drives a single :class:`NonLinearFluxVector`, recording the compensated
    offsets (``get_corrected_offsets``) and play waveforms (``get_corrected_play``) in their order of
    creation; a second *rewrite* pass (``handle_non_linear``) replays the structure, consuming those
    recordings to emit the compensated ``SetGain`` / ``SetOffset`` / ``Play`` ops.
    """

    def __init__(self, crosstalk: NonLinearCrosstalkMatrix) -> None:
        self._crosstalk = crosstalk
        self._vector = NonLinearFluxVector()
        self._vector.set_crosstalk(crosstalk)
        self._buses = set(crosstalk.matrix.keys())
        self._offsets: list[dict[str, np.ndarray]] = []
        self._plays: list[dict[str, np.ndarray]] = []
        self._active_loops: list[ForLoop | Parallel] = []

    # ------------------------------- collection pass (drives the math object) -------------------------------

    def run(self, qprogram: QProgram) -> None:
        # Collect first (records loop identities via ``id()``), then rewrite the *same* node objects
        # (so the recorded ``id()``\\ s still match — ``apply_crosstalk_compensation`` already copied
        # the whole program once, so mutating in place here is safe).
        self._collect(qprogram.body)
        corrected, _ = self._rewrite(list(qprogram.body.elements))
        qprogram.body._elements = corrected

    @staticmethod
    def _nonlinear_loop_values(loop: ForLoop | Loop) -> np.ndarray:
        """Sweep values as the legacy non-linear path produced them.

        The legacy ``NonLinearFluxVector.set_loop`` builds ``np.linspace(start, stop, iterations)`` for
        a ``ForLoop`` (where ``iterations`` is the legacy ``_iterations_from_loop`` count — a floored
        ``(stop - start + step) / step``), not the ``start + step * arange`` grid the executor uses. We
        replicate that here so the recorded sweep matches the legacy compensation byte-for-byte.
        """
        if isinstance(loop, Loop):
            return np.asarray(loop.values)
        return np.linspace(loop.start, loop.stop, NonLinearFluxVector._iterations_from_loop(loop))

    def _set_loop(self, loop: ForLoop | Parallel) -> None:
        cid = self._vector.curr_loop_id
        if isinstance(loop, Parallel):
            for inner in loop.loops:
                self._vector.variables[inner.variable.id] = self._vector.VariableContext(
                    inner.variable.id, self._nonlinear_loop_values(inner), cid
                )
        else:
            self._vector.variables[loop.variable.id] = self._vector.VariableContext(
                loop.variable.id, self._nonlinear_loop_values(loop), cid
            )
        self._vector.loops[cid] = loop  # type: ignore[assignment]
        self._vector.loops_uuid[cid] = id(loop)  # type: ignore[assignment]
        self._vector.curr_loop_id += 1

    def _exit_loop(self, loop: ForLoop | Parallel) -> None:
        labels: list[str] = []
        if isinstance(loop, ForLoop):
            labels.append(loop.variable.id)
        elif isinstance(loop, Parallel):
            labels.extend(inner.variable.id for inner in loop.loops)
        loop_id = next((self._vector.variables[lbl].loop_ref for lbl in labels if lbl in self._vector.variables), None)
        if loop_id is None:
            return
        last_values = {
            lbl: float(vc.arr[-1]) for lbl, vc in self._vector.variables.items() if vc.loop_ref == loop_id
        }
        for bus in self._vector.offset:
            self._vector.offset[bus] = self._vector._substitute_last_values(self._vector.offset[bus], last_values)
        for bus in self._vector.gain:
            self._vector.gain[bus] = self._vector._substitute_last_values(self._vector.gain[bus], last_values)
        for lbl in [lbl for lbl, vc in self._vector.variables.items() if vc.loop_ref == loop_id]:
            del self._vector.variables[lbl]

    def _register_loop_for(self, value: object) -> None:
        """Register the loop binding ``value`` (a swept variable) with the flux vector, if any."""
        if not isinstance(value, Variable) or value.id in self._vector.variables:
            return
        loop = next(
            (
                lp
                for lp in self._active_loops
                if (isinstance(lp, ForLoop) and lp.variable.id == value.id)
                or (isinstance(lp, Parallel) and any(inner.variable.id == value.id for inner in lp.loops))
            ),
            None,
        )
        if loop is not None:
            self._set_loop(loop)

    def _collect(self, block: Block) -> None:
        play_dict: dict[str, Waveform] = {}
        offset_list: list[str] = []
        for element in block.elements:
            if isinstance(element, _CORE_FLUX_OPS) and element.bus in self._buses:
                if isinstance(element, (SetOffset, SetGain)):
                    if isinstance(element, SetOffset) and element.bus in offset_list:
                        self._offsets.append(self._vector.get_corrected_offsets())
                        offset_list = []
                    elif isinstance(element, SetOffset):
                        offset_list.append(element.bus)
                    value = element.gain if isinstance(element, SetGain) else element.offset_path0
                    self._register_loop_for(value)
                    legacy_value = _to_legacy_expression(value)
                    if isinstance(element, SetGain):
                        self._vector.gain[element.bus] = legacy_value
                    else:
                        self._vector.offset[element.bus] = legacy_value
                elif isinstance(element, Play):
                    if element.bus in play_dict:
                        self._plays.append(self._vector.get_corrected_play(play_dict))
                        self._offsets.append(self._vector.get_corrected_offsets())
                        play_dict = {}
                    play_dict[element.bus] = _single_waveform(element.waveform)
            if isinstance(element, Block):
                if isinstance(element, (ForLoop, Parallel)):
                    self._active_loops.append(element)
                if play_dict:
                    self._plays.append(self._vector.get_corrected_play(play_dict))
                    self._offsets.append(self._vector.get_corrected_offsets())
                    play_dict = {}
                self._collect(element)
                if isinstance(element, (ForLoop, Parallel)):
                    self._active_loops.pop()
        if play_dict:
            self._plays.append(self._vector.get_corrected_play(play_dict))
            self._offsets.append(self._vector.get_corrected_offsets())
            play_dict = {}
        if offset_list:
            self._offsets.append(self._vector.get_corrected_offsets())
            offset_list = []
        if (
            isinstance(block, ForLoop)
            or (isinstance(block, Parallel) and all(isinstance(lp, ForLoop) for lp in block.loops))
        ) and block in self._vector.loops.values():
            self._exit_loop(block)

    # ------------------------------- rewrite pass (consumes the recordings) -------------------------------

    def _rewrite(  # faithful port of the legacy handle_non_linear traversal
        self,
        elements: list,
        loop_index: tuple[int, ...] = (),
        loop_coord: tuple[int, ...] = (),
        offsets_0: int = 0,
        plays_0: int = 0,
        offset_defined: bool = False,
        wait_defined: bool = False,
    ) -> tuple[list, bool]:
        corrected: list = []
        offsets_index = offsets_0
        last_appended_offset = -1
        plays_index = plays_0
        play_bus_list: list[str] = []
        flux_buses = sorted(self._buses)

        if not loop_coord:
            loop_coord = (0,)

        for element in elements:
            if isinstance(element, SetGain) and element.bus in self._buses:
                continue
            if isinstance(element, SetOffset) and element.bus in self._buses:
                if offsets_index != last_appended_offset:
                    if wait_defined:
                        offsets_index += 1
                    for bus in flux_buses:
                        corrected.append(SetOffset(bus, float(self._offsets[offsets_index][bus][loop_coord])))
                    last_appended_offset = offsets_index
                    offset_defined = True
            elif isinstance(element, Play) and element.bus in self._buses:
                if not play_bus_list or element.bus in play_bus_list:
                    play_bus_list.append(element.bus)
                    for bus in flux_buses:
                        corrected_waveform = self._plays[plays_index][bus][loop_coord]
                        new_waveform, amplitude = self._convert_corrected_waveform(corrected_waveform)
                        corrected.append(SetGain(bus, amplitude))
                        if not offset_defined:
                            corrected.append(SetOffset(bus, float(self._offsets[offsets_index][bus][loop_coord])))
                        corrected.append(self._rebuild_play(element, bus, new_waveform))
                    plays_index += 1
                    offsets_index += 1
                    offset_defined = True
            elif isinstance(element, Wait) and element.bus in self._buses:
                corrected.append(element)
                if offset_defined:
                    offset_defined = False
                    wait_defined = True
                    last_appended_offset = -1
            elif isinstance(element, Block):
                if id(element) in self._vector.loops_uuid.values():
                    shape = next(iter(self._offsets[offsets_index].values())).shape
                    for key in range(shape[-len(loop_index) - 1]):
                        loop_coord = (key, *loop_index[::-1])
                        corrected_loop, offset_defined = self._rewrite(
                            element.elements,
                            loop_index=(*loop_index, key),
                            loop_coord=loop_coord,
                            offsets_0=offsets_index,
                            plays_0=plays_index,
                        )
                        corrected.extend(corrected_loop)
                else:
                    corrected_loop, offset_defined = self._rewrite(
                        element.elements,
                        loop_index=loop_index,
                        loop_coord=loop_coord,
                        offsets_0=offsets_index,
                        plays_0=plays_index,
                    )
                    element_copy = deepcopy(element)
                    element_copy._elements = corrected_loop
                    corrected.append(element_copy)
                if offset_defined:
                    offsets_index += 1
                    offset_defined = False
            else:
                corrected.append(element)

        if corrected and not isinstance(corrected[-1], Sync):
            corrected.append(Sync())
        return corrected, offset_defined

    @staticmethod
    def _convert_corrected_waveform(corrected_waveform: object) -> tuple[Waveform, float]:
        """Convert a ``get_corrected_play`` waveform (a *legacy* qililab waveform) to a new-AST one.

        ``NonLinearFluxVector.get_corrected_play`` builds ``qililab.waveforms`` ``Square`` /
        ``Arbitrary`` objects. A constant ``Square`` is normalised to amplitude 1 with the amplitude
        folded into a :class:`~qprogram.operations.SetGain` (more efficient on hardware); anything else
        becomes a new-AST :class:`~qprogram.waveforms.Arbitrary` with unit gain. Returns
        ``(new_waveform, gain)``.
        """
        amplitude = getattr(corrected_waveform, "amplitude", None)
        duration = getattr(corrected_waveform, "duration", None)
        if amplitude is not None and duration is not None and not hasattr(corrected_waveform, "samples"):
            return Square(amplitude=1, duration=int(duration)), float(amplitude)
        samples = np.asarray(corrected_waveform.envelope())  # type: ignore[attr-defined]
        return Arbitrary(samples=samples), 1.0

    @staticmethod
    def _rebuild_play(template: Play, bus: str, waveform: Waveform) -> Play:
        return Play(bus=bus, waveform=waveform)


# --------------------------------------------------------------------------- qdac linear lowering


class _QdacLinearLowering:
    """Linear crosstalk lowering for the qdac vendor flux family.

    A port of the legacy ``with_crosstalk_qdac``: build a :class:`FluxVector` seeded from the QDAC
    resting bias (``set_crosstalk_from_bias`` — but with a zero resting bias since the new model has
    no separate ``qdac_buses_offset`` arg here), accumulate the per-bus target flux from each group of
    flux ops, then replace the group with one compensated qdac op per crosstalk bus
    (:class:`~qprogram_qdac.operations.SetOffset` for a scalar bias, :class:`~qprogram_qdac.operations.Play`
    of an :class:`~qprogram.waveforms.Arbitrary` for an array bias).
    """

    def __init__(self, crosstalk: CrosstalkMatrix) -> None:
        self._crosstalk = crosstalk
        self._buses = list(crosstalk.matrix.keys())

    def run(self, qprogram: QProgram) -> None:
        self._traverse(qprogram.body)

    def _traverse(self, block: Block) -> None:
        for element in block.elements:
            if isinstance(element, Block):
                self._traverse(element)
        self._compensate_block(block)

    def _compensate_block(self, block: Block) -> None:
        # Collect the indices + target flux of the qdac flux ops in this block (legacy collected all of
        # the block's flux ops into one vector, then inserted the compensated ops at the first index).
        indices: list[int] = []
        play_template: QdacPlay | None = None
        flux_vector = FluxVector()
        flux_vector.set_crosstalk_from_bias(self._crosstalk, dict.fromkeys(self._buses, 0.0))
        for i, element in enumerate(block.elements):
            if _QDAC_FLUX_OPS and isinstance(element, _QDAC_FLUX_OPS) and element.bus in self._buses:
                indices.append(i)
                if isinstance(element, QdacPlay):
                    flux_vector.flux_vector[element.bus] = element.waveform.envelope()
                    play_template = element
                elif isinstance(element, QdacSetOffset):
                    flux_vector.flux_vector[element.bus] = self._scalar(element.offset)
        if not indices:
            return

        flux_vector.update_bias_vector()
        replacement: list = []
        for bus in self._buses:
            bias = flux_vector.bias_vector[bus]
            if isinstance(bias, (np.ndarray, list)):
                replacement.append(self._make_play(bus, np.asarray(bias), play_template))
            else:
                replacement.append(QdacSetOffset(bus, float(bias)))

        # Remove the original flux ops and splice in the compensated ones at the first flux index.
        first = indices[0]
        for offset, idx in enumerate(indices):
            block._elements.pop(idx - offset)
        block._elements[first:first] = replacement

    @staticmethod
    def _scalar(value: object) -> float:
        if isinstance(value, Expression):
            return float(value.evaluate_or_raise())
        return float(value)

    @staticmethod
    def _make_play(bus: str, samples: np.ndarray, template: QdacPlay | None) -> QdacPlay:
        if template is not None:
            return QdacPlay(
                bus=bus,
                waveform=Arbitrary(samples),
                dwell=template.dwell,
                delay=template.delay,
                repetitions=template.repetitions,
                stepped=template.stepped,
            )
        return QdacPlay(bus=bus, waveform=Arbitrary(samples))


__all__ = ["apply_crosstalk_compensation", "extract_crosstalk"]
