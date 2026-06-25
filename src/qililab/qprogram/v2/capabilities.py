"""Build qililab's :class:`~qprogram.protocol.PlatformCapabilities` for the new ``qprogram``.

This module is deliberately free of any ``qililab`` import — it depends only on the standalone
``qprogram`` package (plus the ``qprogram_qblox`` / ``qprogram_qdac`` vendor extensions) so it can
be unit-tested in isolation. It authors two qililab capability profiles whose predicates encode the
restrictions the legacy Qblox/QDAC compilers enforce, and exposes :func:`qililab_capabilities` to
assemble the per-bus descriptor a platform advertises.

The capability recipe mirrors :func:`qprogram.executor.reference_capabilities`:

* The **platform slot** carries control-flow / expression / ``measure.returns`` tokens and the
  bus-less orchestration ops. Its *hw* half excludes ``op.set_parameter`` / ``op.get_parameter`` /
  ``op.set_crosstalk`` (those are software-dispatched), while its *sw* half keeps them. Both halves
  ship :func:`_swept_parameter_forces_software`, so a loop that sweeps a ``set_parameter`` value is
  forced out of real-time hardware and becomes a software (host-driven) outer loop.
* Each **bus slot** is filled by a vendor profile: a Qblox bus is real-time hardware
  (``hw=...``, ``sw=None``); a QDAC bus is a slow DC source with no FPGA (``hw=None``, ``sw=...``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import qprogram_qblox  # noqa: F401  (side effect: registers ``qblox-default-v1`` + qblox tokens)
import qprogram_qdac  # noqa: F401  (side effect: registers ``qdac-default-v1`` + qdac tokens)
from qprogram.operations import Measure, Play, SetOffset, SetParameter
from qprogram.protocol import (
    BusCapabilities,
    CompilerCapabilities,
    Diagnostic,
    DomainConstraint,
    PlatformCapabilities,
    Profile,
    register_profile,
)
from qprogram.variable import Constant, Expression, Variable

from qililab.qprogram.v2.vendor import SET_CROSSTALK_TOKEN, register_qililab_vendor

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from qprogram.blocks.block import Block
    from qprogram.operations.operation import Operation
    from qprogram.protocol import ValidationContext

#: Bus-less orchestration ops that are software-dispatched, never real-time. Excluded from the
#: platform slot's *hw* half so a program that uses them classifies (and a loop sweeping them
#: forces) to software — exactly mirroring ``qprogram.executor.reference_capabilities``. The core
#: only ships ``op.set_parameter`` / ``op.get_parameter``; qililab's private ``set_crosstalk`` is a
#: vendor op (``vendor.qililab.set_crosstalk``) added to the platform slot's *sw* half below.
_BUS_LESS_OPS = frozenset({"op.set_parameter", "op.get_parameter", SET_CROSSTALK_TOKEN})

#: Tokens removed from the platform slot's *hw* half. Beyond the orchestration ops, ``sweep.arbitrary``
#: is excluded because neither Qblox nor QDAC can run an arbitrary-value sweep in real time — an
#: arbitrary ``Loop`` is therefore software-only (legal only as an unrolled outer loop).
_PLATFORM_HW_EXCLUDE = _BUS_LESS_OPS | frozenset({"sweep.arbitrary"})

#: Names of the qililab profiles authored here.
QBLOX_PROFILE_NAME = "qililab-qblox-v1"
QDAC_PROFILE_NAME = "qililab-qdac-v1"
PLATFORM_PROFILE_NAME = "qililab-platform-v1"


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def _is_swept(value: object) -> bool:
    """Return whether ``value`` is a non-constant symbolic expression (a swept value).

    A plain ``int``/``float`` is not an :class:`~qprogram.variable.Expression`; a
    :class:`~qprogram.variable.Constant` is an Expression but folds to a literal; a
    :class:`~qprogram.variable.Variable` (or any compound node) is a genuine sweep.
    """
    return isinstance(value, Expression) and not isinstance(value, Constant)


def _swept_parameter_forces_software(
    node: Operation | Block,
    ctx: ValidationContext,
) -> Iterable[Diagnostic | DomainConstraint]:
    """Force the binding loop of a swept ``set_parameter`` value out of real-time hardware.

    ``set_parameter`` is a software op; when its value is a loop-swept :class:`~qprogram.Variable`,
    the enclosing loop must be dispatched one iteration at a time from software. The constraint
    targets the *loop block* (never the op) per the validator's contract.
    """
    if isinstance(node, SetParameter) and isinstance(node.value, Variable):
        loop = ctx.binding_loop_of(node.value)
        if loop is not None:
            yield DomainConstraint(
                node=loop,
                exclude=frozenset({"hw"}),
                reason=(
                    f"parameter {node.parameter!r} is swept via set_parameter "
                    "(software dispatch, one iteration per hardware execution)"
                ),
            )


def _swept_waveform_param_forces_software(
    node: Operation | Block,
    ctx: ValidationContext,
) -> Iterable[Diagnostic | DomainConstraint]:
    """Force the binding loop of a swept *waveform parameter* out of real-time hardware.

    Qblox precomputes a waveform's samples at upload time and cannot recompute an envelope between
    real-time loop iterations (legacy ``qblox_compiler`` simply rejects a ``Variable`` inside a
    waveform). In the unified QProgram a waveform parameter *can* still be swept — by an **outer
    software loop** that re-uploads per iteration — so the right classification is a soft
    :class:`~qprogram.DomainConstraint` lifting the binding loop to software, not a hard error. This
    generalises ``qblox-default-v1``'s drag-sigma predicate to every waveform parameter. The
    ``Play`` / ``Measure`` op itself stays hardware; only the loop's iteration mechanism changes.

    For ``Play`` / ``Measure`` / qblox ``Acquire`` the only variable-bearing attributes are the
    waveform / weights, so :meth:`~qprogram.operations.Operation.variables` is exactly the set of
    swept waveform parameters. A waveform parameter that is not loop-bound is a constant at upload
    time and is unaffected. If the binding loop is an inner hardware loop, lifting it to software
    leaves hardware ops stranded in a software loop, which the structural check then reports.
    """
    targets: tuple[type, ...] = (Play, Measure)
    try:
        from qprogram_qblox.operations import Acquire
    except ImportError:  # pragma: no cover - qblox extension always present in qililab
        pass
    else:
        targets = (*targets, Acquire)
    if not isinstance(node, targets):
        return
    seen: set[int] = set()
    for var in node.variables():
        loop = ctx.binding_loop_of(var)
        if loop is None or id(loop) in seen:
            continue
        seen.add(id(loop))
        yield DomainConstraint(
            node=loop,
            exclude=frozenset({"hw"}),
            reason=(
                f"variable {var.id!r} sweeps a waveform parameter in a contained "
                f"{type(node).__name__}; Qblox cannot real-time-update waveform samples, so the "
                f"loop dispatches per shot from software."
            ),
        )


def _reject_wait_trigger_variable_duration(
    node: Operation | Block,
    ctx: ValidationContext,
) -> Iterable[Diagnostic | DomainConstraint]:
    """Reject a Qblox ``wait_trigger`` whose duration is a swept value (must be a constant int)."""
    try:
        from qprogram_qblox.operations import WaitTrigger
    except ImportError:  # pragma: no cover - qblox extension always present in qililab
        return
    if isinstance(node, WaitTrigger) and _is_swept(node.duration):
        yield Diagnostic(
            severity="error",
            code="qililab.qblox.wait-trigger-variable-duration",
            message="Qblox wait_trigger duration must be a constant integer, not a swept value.",
            node=node,
        )


def _reject_differing_iq_offset_expression(
    node: Operation | Block,
    ctx: ValidationContext,
) -> Iterable[Diagnostic | DomainConstraint]:
    """Reject a Qblox ``set_offset`` with a differing-path swept expression.

    The legacy compiler can only write the *same* swept expression to both I/Q paths: a
    ``VariableExpression`` on ``offset_path1``, or on ``offset_path0`` while ``offset_path1`` is
    also set, is unsupported.
    """
    if isinstance(node, SetOffset) and (
        _is_swept(node.offset_path1) or (_is_swept(node.offset_path0) and node.offset_path1 is not None)
    ):
        yield Diagnostic(
            severity="error",
            code="qililab.qblox.iq-offset-expression",
            message="Qblox does not support a differing I/Q offset when using a swept expression.",
            node=node,
        )


# NOTE: ForLoop already rejects ``step == 0`` at construction time (qprogram.blocks.ForLoop), so no
# predicate is needed for that legacy ``_calculate_iterations`` guard.
#
# NOTE: the legacy compiler rejects arbitrary-array ``Loop`` blocks on Qblox (only affine ``ForLoop``
# is realizable as a register sweep). We express that as a *token* rather than a predicate: the
# platform slot's ``hw`` half omits ``sweep.arbitrary`` (see ``_PLATFORM_HW_EXCLUDE``), so an
# arbitrary ``Loop`` classifies software-only — which is correct, since an arbitrary sweep is legal
# as an (unrolled) software outer loop even though Qblox cannot run it in real time.
#
# QDAC variable-in-waveform is already handled softly by ``qdac-default-v1``'s inherited
# ``_qdac_op_with_swept_var_is_software_only`` predicate (QDAC has no FPGA, so every swept value is
# software), so ``qililab-qdac-v1`` needs no extra predicate for it.


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

#: Real-time Qblox bus profile. Inherits every ``qblox-default-v1`` token; layers a minimum-wait
#: limit and the AST-shape predicates the legacy compiler enforces.
_QBLOX_PROFILE = Profile(
    name=QBLOX_PROFILE_NAME,
    version=(0, 1, 0),
    extends="qblox-default-v1",
    capabilities=frozenset(),
    limits={"min_wait_duration_ns": 4},
    predicates=(
        _swept_waveform_param_forces_software,
        _reject_wait_trigger_variable_duration,
        _reject_differing_iq_offset_expression,
    ),
)

#: Slow-DAC QDAC bus profile. Inherits ``qdac-default-v1`` tokens and its
#: ``_qdac_op_with_swept_var_is_software_only`` predicate (which already lifts any swept QDAC value
#: to software), so it needs no extra predicate of its own.
_QDAC_PROFILE = Profile(
    name=QDAC_PROFILE_NAME,
    version=(0, 1, 0),
    extends="qdac-default-v1",
    capabilities=frozenset(),
)


def register_qililab_profiles() -> None:
    """Register qililab's authored profiles. Idempotent (safe to import twice)."""
    register_profile(_QBLOX_PROFILE)
    register_profile(_QDAC_PROFILE)


# Register as an import side effect, mirroring the vendor packages. Registering the qililab vendor
# first puts ``vendor.qililab.set_crosstalk`` in the capability registry so the platform slot can name it.
register_qililab_vendor()
register_qililab_profiles()


# ---------------------------------------------------------------------------
# Capability assembly
# ---------------------------------------------------------------------------


def _platform_compiler_caps(tokens: frozenset[str]) -> CompilerCapabilities:
    """Build the platform-slot :class:`~qprogram.protocol.CompilerCapabilities` for ``tokens``.

    Constructed directly (rather than via ``from_profile``) because we must *subtract* the bus-less
    orchestration ops from the hardware half, which profile inheritance cannot express.
    """
    return CompilerCapabilities(
        profile=PLATFORM_PROFILE_NAME,
        version=(0, 1, 0),
        capabilities=frozenset(tokens),
        limits={},
        predicates=(_swept_parameter_forces_software,),
        vendor_versions={},
    )


def _platform_slot() -> BusCapabilities:
    """The platform-wide slot: control flow / expressions / bus-less ops, with the hw/sw split."""
    base_tokens = CompilerCapabilities.from_profile("qprogram-base-v1").capabilities
    # qililab's vendor ``set_crosstalk`` is a bus-less, software-only orchestration op: present in the
    # sw half, absent from the hw half (so a flux/crosstalk program classifies + dispatches in software).
    sw_tokens = base_tokens | {SET_CROSSTALK_TOKEN}
    return BusCapabilities(
        hw=_platform_compiler_caps(base_tokens - _PLATFORM_HW_EXCLUDE),
        sw=_platform_compiler_caps(sw_tokens),
    )


def qililab_capabilities(bus_specs: Mapping[tuple[str, str], str]) -> PlatformCapabilities:
    """Assemble the qililab :class:`~qprogram.protocol.PlatformCapabilities`.

    Args:
        bus_specs: Maps each ``(element, bus_kind)`` selector — e.g. ``("q", "drive")`` — to the
            backend that drives it: ``"qblox"`` (real-time hardware) or ``"qdac"`` (slow DC source,
            software-dispatched). Typically derived from the platform's runcard.

    Returns:
        The full descriptor: per-bus slots from ``bus_specs``, the shared platform slot, and a
        Qblox default-bus profile fallback for raw-string buses.

    Raises:
        ValueError: If a backend value is not ``"qblox"`` or ``"qdac"``.
    """
    qblox_cc = CompilerCapabilities.from_profile(QBLOX_PROFILE_NAME)
    qdac_cc = CompilerCapabilities.from_profile(QDAC_PROFILE_NAME)
    qblox_bus = BusCapabilities(hw=qblox_cc, sw=None)
    qdac_bus = BusCapabilities(hw=None, sw=qdac_cc)

    bus: dict[tuple[str, str], BusCapabilities] = {}
    for selector, backend in bus_specs.items():
        if backend == "qblox":
            bus[selector] = qblox_bus
        elif backend == "qdac":
            bus[selector] = qdac_bus
        else:
            msg = f"Unknown backend {backend!r} for bus {selector!r}; expected 'qblox' or 'qdac'."
            raise ValueError(msg)

    return PlatformCapabilities(
        bus=bus,
        platform=_platform_slot(),
        default_bus_profile=qblox_bus,
    )
