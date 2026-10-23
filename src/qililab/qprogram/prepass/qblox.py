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

"""Qblox pre-pass: prepares a QProgram for the Qblox compiler, after the shared pre-pass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qililab.config import logger
from qililab.constants import QDACCONSTANTS
from qililab.core.variables import Variable
from qililab.qprogram.blocks import Average, Block, Conditional, ForLoop
from qililab.qprogram.operations import (
    Acquire,
    Measure,
    MeasureReset,
    Play,
    PlayWithCalibratedWaveform,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetMarkers,
    SetOffset,
    SetPhase,
    SetTrigger,
    Sync,
    Wait,
    WaitTrigger,
)
from qililab.qprogram.prepass.shared import keep_operations_on_buses

if TYPE_CHECKING:
    from uuid import UUID

    from qililab.pulse_distortion.pulse_distortion import PulseDistortion
    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
    from qililab.qprogram.operations import Operation
    from qililab.qprogram.qprogram import QProgram

# Default and minimum for qp.if_trigger()'s trigger_padding_ns.
WAIT_TRIGGER_NETWORK_EXT_TRIGGER = 252

# Operations carrying no duration
NON_REALTIME_OPERATIONS = (SetFrequency, SetPhase, ResetPhase, SetGain, SetOffset, SetMarkers)


@dataclass(frozen=True)
class ConditionalTrigger:
    """The ``qp.if_trigger()`` block of a QProgram, once validated."""

    bus: str
    """The Qblox bus the block gates."""

    expected_wait_time_ns: int
    """Expected time (ns) between two external triggers, given or derived from a QDAC dwell."""

    trigger_padding_ns: int
    """Padding (ns) inserted before checking the trigger."""


@dataclass(frozen=True)
class QbloxPrepassResult:
    """What the Qblox pre-pass hands to the Qblox compiler."""

    qprogram: QProgram
    """The transformed QProgram, with only the operations on Qblox buses."""

    acquisition_metadata: dict[str, dict[UUID, tuple[int, int]]]
    """Per Qblox bus and per block: the number of acquisitions directly in the block, and the block's nesting depth."""

    conditional: ConditionalTrigger | None
    """The ``qp.if_trigger()`` block, if any."""

    requires_external_trigger: bool
    """Whether the sequences wait on the cluster's external trigger: a ``wait_trigger`` on a Qblox bus, or an
    ``if_trigger``."""

    latch_enabled: list[str]
    """Qblox buses that need the trigger latch: the control buses of ``measure_reset``."""

    trigger_network_required: dict[str, int]
    """Qblox buses that send on the trigger network, with their trigger address: the measurement buses of
    ``measure_reset``."""


def prepare_qblox(
    qprogram: QProgram,
    *,
    calibration: Calibration | None = None,
    crosstalk: CrosstalkMatrix | None = None,
    bus_distortions: dict[str, list[PulseDistortion]] | None = None,
    qblox_buses: list[str] | None = None,
) -> QbloxPrepassResult:
    """Prepare a QProgram, already through the shared pre-pass, for the Qblox compiler.

    Applies the crosstalk compensation (the calibration's AC matrix, else the given one, else the calibration's DC
    matrix with a warning) and the bus distortions. Then walks the whole QProgram, including operations on other
    instruments, to collect the acquisition metadata, validate ``qp.if_trigger()`` and ``qp.qblox.measure_reset()``,
    and find the trigger requirements. Finally keeps only the operations on Qblox buses.

    Args:
        qprogram (QProgram): The QProgram returned by the shared pre-pass. It is not modified.
        calibration (Calibration, optional): Calibration holding the crosstalk matrices. Defaults to None.
        crosstalk (CrosstalkMatrix, optional): Crosstalk matrix used if the calibration has no AC matrix. Defaults to None.
        bus_distortions (dict[str, list[PulseDistortion]], optional): Distortions to apply per bus. Defaults to None.
        qblox_buses (list[str], optional): The Qblox buses. Defaults to every bus of the QProgram.

    Returns:
        QbloxPrepassResult: The QProgram with only Qblox operations, and what the compiler needs to know about it.

    Raises:
        ValueError: If a ``qp.qblox.measure_reset()`` measures or resets on a bus that isn't a Qblox bus, or if a
            ``qp.if_trigger()`` block has no operation on a Qblox bus, no wait time given or derivable from a QDAC
            ``set_trigger(position='step')`` + ``play(dwell=...)``, or a ``trigger_padding_ns`` below the trigger
            network's propagation delay.
        NotImplementedError: If ``qp.if_trigger()`` is used in a way that isn't supported.
    """
    if calibration is not None:
        if calibration.crosstalk_matrix_ac is not None:
            crosstalk = calibration.crosstalk_matrix_ac
        elif crosstalk is None and calibration.crosstalk_matrix is not None:
            logger.warning(
                "Using DC `crosstalk_matrix`.\nDefine `crosstalk_matrix_ac` to calibrate AC/fast-flux lines."
            )
            crosstalk = calibration.crosstalk_matrix
    if crosstalk is not None:
        qprogram = qprogram.with_crosstalk_qblox(crosstalk=crosstalk)
    if bus_distortions is not None:
        qprogram = qprogram.with_distortions(bus_distortions=bus_distortions)

    qblox_buses = qblox_buses or list(qprogram.buses)
    leaves, acquisition_metadata, conditional_block = _walk_tree(qprogram.body, qblox_buses)

    conditional = None
    if conditional_block is not None:
        element, start, end = conditional_block
        conditional = _validate_conditional_trigger(element, (start, end), leaves, qblox_buses)
        _validate_conditional_bus_isolation(conditional.bus, (start, end), leaves, qprogram.buses & set(qblox_buses))

    measure_resets = [leaf for leaf in leaves if isinstance(leaf, MeasureReset)]
    for measure_reset in measure_resets:
        if measure_reset.bus not in qblox_buses or measure_reset.control_bus not in qblox_buses:
            raise ValueError(
                f"qp.qblox.measure_reset() measures on bus '{measure_reset.bus}' and resets on bus "
                f"'{measure_reset.control_bus}', but both must be Qblox buses; the Qblox buses are {sorted(qblox_buses)}."
            )

    return QbloxPrepassResult(
        qprogram=keep_operations_on_buses(qprogram, set(qblox_buses)),
        acquisition_metadata=acquisition_metadata,
        conditional=conditional,
        requires_external_trigger=conditional is not None
        or any(isinstance(leaf, WaitTrigger) and leaf.bus in qblox_buses for leaf in leaves),
        latch_enabled=list(dict.fromkeys(measure_reset.control_bus for measure_reset in measure_resets)),
        trigger_network_required={measure_reset.bus: measure_reset.trigger_address for measure_reset in measure_resets},
    )


def _walk_tree(
    body: Block, qblox_buses: list[str]
) -> tuple[list[Operation], dict[str, dict[UUID, tuple[int, int]]], tuple[Conditional, int, int] | None]:
    """Walk the QProgram once, before the bus filter, since ``qp.if_trigger()`` needs the QDAC operations.

    Returns:
        tuple: The flat, document-order list of every non-``Block`` operation (the leaves); the acquisition metadata of
        the Qblox buses (bus -> block uuid -> (acquisitions directly in the block, block depth)); and the
        ``qp.if_trigger()`` block, if any, with the ``(start, end)`` range of its leaves.

    Raises:
        NotImplementedError: If a block other than ``qp.average(...)``/``qp.for_loop(...)`` is nested inside
            ``qp.if_trigger()``, or if there is more than one ``qp.if_trigger()`` block.
    """
    leaves: list[Operation] = []
    acquisition_metadata: dict[str, dict[UUID, tuple[int, int]]] = {}
    conditional_block: tuple[Conditional, int, int] | None = None

    def traverse(block: Block, depth: int, inside_conditional: bool) -> None:
        nonlocal conditional_block
        for element in block.elements:
            if isinstance(element, Block):
                if inside_conditional and not isinstance(element, (Average, ForLoop)):
                    raise NotImplementedError(
                        f"{type(element).__name__} block cannot be nested inside qp.if_trigger() "
                        "(only qp.average(...)/qp.for_loop(...) can be)."
                    )
                start = len(leaves)
                traverse(element, depth + 1, inside_conditional or isinstance(element, Conditional))
                if isinstance(element, Conditional):
                    if conditional_block is not None:
                        raise NotImplementedError("Only one qp.if_trigger() block is supported per QProgram.")
                    conditional_block = (element, start, len(leaves))
            else:
                leaves.append(element)
                if isinstance(element, (Acquire, Measure, MeasureReset)) and element.bus in qblox_buses:
                    block_metadata = acquisition_metadata.setdefault(element.bus, {})
                    count, _ = block_metadata.get(block.uuid, (0, depth))
                    block_metadata[block.uuid] = (count + 1, depth)

    traverse(body, 0, False)
    return leaves, acquisition_metadata, conditional_block


def _validate_conditional_trigger(
    element: Conditional, leaf_range: tuple[int, int], all_leaves: list[Operation], qblox_buses: list[str]
) -> ConditionalTrigger:
    """Validate a ``qp.if_trigger()`` block and resolve the bus it gates and its wait time.

    Raises:
        NotImplementedError: If the block contains a ``qp.wait(duration=<variable>)``, touches more than one Qblox
            bus, or if more than one Qblox bus is compiled at all.
        ValueError: If no operation in the block is on a Qblox bus, if ``expected_wait_time_ns`` isn't given and can't
            be derived from a QDAC ``set_trigger(position='step')`` + ``play(dwell=...)``, or if
            ``trigger_padding_ns`` is below the trigger network's propagation delay.
    """
    start, end = leaf_range
    leaves = all_leaves[start:end]
    dynamic_wait = next((x for x in leaves if isinstance(x, Wait) and isinstance(x.duration, Variable)), None)
    if dynamic_wait is not None:
        raise NotImplementedError(
            f"qp.wait(bus='{dynamic_wait.bus}', duration=<variable>) cannot be used inside "
            "qp.if_trigger(): its duration must be a compile-time constant for the trigger-cadence "
            "padding to account for it, wherever that variable comes from."
        )

    conditional_bus = {x.bus for x in leaves if hasattr(x, "bus") and x.bus in qblox_buses}
    if len(conditional_bus) > 1:
        raise NotImplementedError(
            "Conditional instructions based on a trigger can only be associated with one bus for now."
        )

    if not conditional_bus:
        raise ValueError("qp.if_trigger()'s body must contain at least one instruction on a qblox bus to gate.")

    if len(qblox_buses) > 1:
        raise NotImplementedError(
            f"qp.if_trigger() only supports compiling a single qblox bus for now; got {sorted(qblox_buses)}."
        )

    bus = next(iter(conditional_bus))
    expected_wait_time_ns = element.expected_wait_time_ns
    if expected_wait_time_ns is None:
        expected_wait_time_ns = _derive_expected_wait_time_from_qdac(all_leaves, qblox_buses)
    if expected_wait_time_ns is None:
        raise ValueError(
            f"qp.if_trigger() on bus '{bus}' has no expected_wait_time_ns and no QDAC "
            "set_trigger(position='step') + play(dwell=...) in this QProgram to derive it from."
        )

    if element.trigger_padding_ns is not None and element.trigger_padding_ns < WAIT_TRIGGER_NETWORK_EXT_TRIGGER:
        raise ValueError(
            f"qp.if_trigger()'s trigger_padding_ns ({element.trigger_padding_ns}) cannot be lower than "
            f"{WAIT_TRIGGER_NETWORK_EXT_TRIGGER} ns, the trigger network's propagation delay."
        )

    return ConditionalTrigger(
        bus=bus,
        expected_wait_time_ns=expected_wait_time_ns,
        trigger_padding_ns=(
            element.trigger_padding_ns if element.trigger_padding_ns is not None else WAIT_TRIGGER_NETWORK_EXT_TRIGGER
        ),
    )


def _derive_expected_wait_time_from_qdac(leaves: list[Operation], qblox_buses: list[str]) -> int | None:
    """Derive the external-trigger wait time (ns) from a QDAC trigger set up in this same QProgram.

    ``qp.set_trigger(bus, ..., position="step")`` fires the trigger once per sweep step, so the inter-trigger period
    equals that step's ``dwell`` (set via ``qp.qdac.play(bus, ..., dwell=...)``, in microseconds). Returns ``None`` if
    no such trigger is found, e.g. the trigger source isn't a QDAC modeled in this QProgram.

    Raises:
        NotImplementedError: If a ``qp.set_trigger()`` on a QDAC-driven bus has a ``position`` other than ``"step"``,
            or if more than one bus has a ``qp.set_trigger(position="step")``: which one is wired to the trigger
            address ``qp.if_trigger()`` gates on cannot be inferred from the QProgram alone.
        ValueError: If a ``qp.set_trigger(position="step")`` has no preceding ``qp.qdac.play(bus, dwell=...)``.
    """
    dwell_us_by_bus: dict[str, int] = {}
    step_trigger_wait_time_by_bus: dict[str, int] = {}

    for element in leaves:
        if isinstance(element, (Play, PlayWithCalibratedWaveform)):
            if element.bus not in qblox_buses and element.bus not in dwell_us_by_bus:
                # A falsy (unset or 0) dwell mirrors the QDAC compiler's own default. Qblox buses are excluded so a
                # plain qp.play() on the gated bus itself is never mistaken for a QDAC-driven bus.
                dwell_us_by_bus[element.bus] = element.dwell or QDACCONSTANTS.DEFAULT_DWELL_US
        elif isinstance(element, SetTrigger):
            if element.position == "step":
                if element.bus not in dwell_us_by_bus:
                    raise ValueError(
                        f"qp.set_trigger(bus='{element.bus}', position='{element.position}') has no "
                        f"preceding qp.qdac.play(bus='{element.bus}', dwell=...) in this QProgram to "
                        "derive its wait time from."
                    )
                step_trigger_wait_time_by_bus[element.bus] = dwell_us_by_bus[element.bus] * 1000
            elif element.bus in dwell_us_by_bus:
                # Only buses already known to be QDAC-driven must use position="step"; a qp.set_trigger() on an
                # unrelated bus (e.g. a Qblox marker trigger) isn't part of this derivation.
                raise NotImplementedError(
                    f"qp.if_trigger() requires qp.set_trigger(bus='{element.bus}', position='step'); "
                    f"got position='{element.position}'."
                )

    if len(step_trigger_wait_time_by_bus) > 1:
        raise NotImplementedError(
            "Cannot derive qp.if_trigger()'s expected_wait_time_ns automatically: found "
            f"qp.set_trigger(position='step') on more than one bus ({sorted(step_trigger_wait_time_by_bus)}); "
            "pass expected_wait_time_ns explicitly to disambiguate which one gates the trigger."
        )
    return next(iter(step_trigger_wait_time_by_bus.values()), None)


def _validate_conditional_bus_isolation(
    bus: str, leaf_range: tuple[int, int], all_leaves: list[Operation], qblox_buses_in_qprogram: set[str]
) -> None:
    """Ensure the bus gated by ``qp.if_trigger()`` has no real-time instruction outside the block.

    The epilogue's padding only balances the time spent inside the ``Conditional`` block; a real-time instruction on
    the same bus outside it would drift the sequencer out of phase with the QDAC's trigger cadence.
    ``NON_REALTIME_OPERATIONS`` (``qp.set_frequency()``, ``qp.set_offset()``, ...) add no duration, so are allowed.

    Raises:
        NotImplementedError: If a real-time instruction on ``bus`` is outside the block.
    """
    start, end = leaf_range

    def touches_bus(x: Operation) -> bool:
        if isinstance(x, NON_REALTIME_OPERATIONS):
            return False
        if isinstance(x, Sync):
            return bus in (x.buses or qblox_buses_in_qprogram)
        return getattr(x, "bus", None) == bus

    outside = [x for i, x in enumerate(all_leaves) if touches_bus(x) and not start <= i < end]
    if outside:
        raise NotImplementedError(
            f"Bus '{bus}' cannot have instructions outside its qp.if_trigger() block: found "
            f"{type(outside[0]).__name__} outside the conditional, which would break the synchronisation."
        )
