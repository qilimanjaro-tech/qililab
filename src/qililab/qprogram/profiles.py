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
"""The capability profile listing what qililab can run: ``qililab-qblox-parity-v1``.

qprogram can describe much more than qililab compiles today. Every program is validated against
[`QILILAB_QBLOX_PARITY_V1`][qililab.qprogram.profiles.QILILAB_QBLOX_PARITY_V1] before compilation, so anything else
fails there with qprogram's ``missing-capability`` (or one of the ``qililab.*`` codes below) instead of compiling to
something wrong.

- Everything runs in real time on the Qblox sequencers, except QDAC operations, which run on the PC as setup before
  the run. So loops are real-time only, and a QDAC operation inside a loop is rejected; a plain ``qp.block()`` may
  hold QDAC operations.
- Loops sweep a ``Range`` only. No conditionals other than ``if_trigger``, no fragment calls, no
  ``set_parameter``/``get_parameter``, no ``qblox.set_acquisition_threshold``/``set_acquisition_rotation``.
- Expressions are a variable, a constant, a negated variable, or one ``+`` or ``-`` between two of those.
- Waveforms are the ones qililab had, with no variable in their parameters.
"""

from collections.abc import Iterable, Iterator
from numbers import Real

import qprogram_qblox  # noqa: F401  (registers the qblox tokens)

# Importing qprogram_qdac also registers the qdac tokens and profile.
import qprogram_qdac
from qprogram import BinaryOp, Constant, Expression, UnaryOp, Variable
from qprogram.protocol import (
    BusCapabilities,
    CompilerCapabilities,
    Diagnostic,
    DomainConstraint,
    PlatformCapabilities,
    Profile,
    ValidationContext,
    register_profile,
    resolve_profile,
)
from qprogram.waveforms import IQWaveform, Waveform

import qililab.qprogram.formats.vendor  # noqa: F401  (registers the qililab tokens)

_BLOCKS = frozenset(
    {
        "block.block",
        "block.average",
        "block.sweep",
        "block.parallel",
        "sweep.linear",
        "sweep.range",
        "vendor.qililab.infinite_loop",
        "vendor.qililab.if_trigger",
    }
)
_EXPRESSIONS = frozenset({"expr.constant", "expr.variable", "expr.binary_op", "expr.unary_op"})

_QBLOX_OPERATIONS = frozenset(
    {
        "op.play",
        "op.measure",
        "op.wait",
        "op.sync",
        "op.set_frequency",
        "op.set_phase",
        "op.set_gain",
        "op.reset_phase",
        "op.set_offset",
        "vendor.qblox.acquire",
        "vendor.qblox.scope",
        "vendor.qblox.set_markers",
        "vendor.qblox.set_trigger",
        "vendor.qblox.wait_trigger",
        "vendor.qililab.measure_reset",
        "vendor.qililab.qblox_play",
        "measure.fields.iq",
        "measure.fields.state",
    }
)
_QDAC_OPERATIONS = frozenset(
    {"vendor.qdac.play", "vendor.qdac.set_offset", "vendor.qdac.set_trigger", "vendor.qdac.wait_trigger"}
)
_QILILAB_WAVEFORMS = frozenset(
    {
        "waveform.alias",
        "waveform.arbitrary",
        "waveform.chained",
        "waveform.flat_top",
        "waveform.gaussian",
        "waveform.gaussian_drag_correction",
        "waveform.ramp",
        "waveform.snz",
        "waveform.square",
        "waveform.iq_drag",
        "waveform.iq_pair",
    }
)


def _waveform_expressions(waveform: object) -> Iterator[Expression]:
    """Yield every expression among a waveform's parameters, nested waveforms included.

    Args:
        waveform (object): A waveform, an IQ waveform, or anything else (which yields nothing).

    Yields:
        Expression: Each expression found.
    """
    if not isinstance(waveform, (Waveform, IQWaveform)):
        return
    for value in vars(waveform).values():
        values = value if isinstance(value, (list, tuple)) else [value]
        for item in values:
            if isinstance(item, Expression):
                yield item
            else:
                yield from _waveform_expressions(item)


def _reject_variable_in_waveform(node: object, ctx: ValidationContext) -> Iterable[Diagnostic | DomainConstraint]:
    """Reject a waveform or weights whose parameters use a variable (e.g. a swept amplitude).

    qililab samples waveforms once, before the run, so it cannot follow a variable inside one.

    Args:
        node (object): The AST node being validated.
        ctx (ValidationContext): Program-wide facts, unused.

    Yields:
        Diagnostic: A ``qililab.variable-in-waveform`` error when a waveform of ``node`` uses a variable.
    """
    for attribute in getattr(node, "WAVEFORM_ATTRS", ()):
        if any(True for _ in _waveform_expressions(getattr(node, attribute, None))):
            yield Diagnostic(
                severity="error",
                code="qililab.variable-in-waveform",
                message=(
                    f"The {attribute} of {type(node).__name__} uses a variable in its parameters, which qililab does "
                    "not support: waveforms are sampled once, before the run. Use constant parameters, and sweep "
                    "the gain or the offset instead of the amplitude."
                ),
                node=node,  # type: ignore[arg-type]
            )


def _is_supported_expression(expression: Expression) -> bool:
    """Return whether qililab can compile ``expression``.

    Args:
        expression (Expression): The expression to check.

    Returns:
        bool: True for a variable, a constant, a negated variable, or one ``+`` or ``-`` between two of those.
    """
    if isinstance(expression, (Variable, Constant)):
        return True
    if isinstance(expression, UnaryOp):
        return expression.op == "-" and isinstance(expression.operand, Variable)
    if isinstance(expression, BinaryOp):
        return expression.op in {"+", "-"} and all(
            isinstance(operand, (Variable, Constant)) for operand in (expression.left, expression.right)
        )
    return False


def _reject_unsupported_arithmetic(node: object, ctx: ValidationContext) -> Iterable[Diagnostic | DomainConstraint]:
    """Reject arithmetic beyond one ``+`` or ``-``: chained (``10 + x + 100``), ``*``, ``/`` and the rest.

    ``*`` and ``/`` share the ``expr.binary_op`` token with ``+`` and ``-``, so the profile cannot leave them out by
    token alone.

    Args:
        node (object): The AST node being validated.
        ctx (ValidationContext): Program-wide facts, unused.

    Yields:
        Diagnostic: A ``qililab.unsupported-arithmetic`` error for each unsupported expression of ``node``.
    """
    for name, value in vars(node).items():
        if not name.startswith("_") and isinstance(value, Expression) and not _is_supported_expression(value):
            yield Diagnostic(
                severity="error",
                code="qililab.unsupported-arithmetic",
                message=(
                    f"The {name} of {type(node).__name__} is {value!r}, which qililab does not support: an expression "
                    "can only be a variable, a constant, a negated variable, or one + or - between two of those."
                ),
                node=node,  # type: ignore[arg-type]
            )


_QDAC_TIME_RANGES: tuple[tuple[type, str, str, float, float], ...] = (
    (qprogram_qdac.Play, "qp.qdac.play", "delay", 0.0, 3600.0),
    (qprogram_qdac.SetTrigger, "qp.qdac.set_trigger", "duration", 1e-6, 3600.0),
)
"""The QDAC-II's range, in seconds, of the QDAC times qprogram-qdac passes through unchecked: (operation, its call,
attribute, minimum, maximum)."""


def _reject_qdac_time_out_of_range(node: object, ctx: ValidationContext) -> Iterable[Diagnostic | DomainConstraint]:
    """Reject a QDAC play delay or trigger width outside what the QDAC-II takes.

    qprogram-qdac only checks the dwell; the delay and the trigger width would otherwise reach the instrument as they
    are.

    Args:
        node (object): The AST node being validated.
        ctx (ValidationContext): Program-wide facts, unused.

    Yields:
        Diagnostic: A ``qililab.qdac-out-of-range`` error when the value is outside the QDAC-II's range.
    """
    for operation, call, attribute, minimum, maximum in _QDAC_TIME_RANGES:
        value = getattr(node, attribute, None) if isinstance(node, operation) else None
        if isinstance(value, Real) and not minimum <= float(value) <= maximum:
            yield Diagnostic(
                severity="error",
                code="qililab.qdac-out-of-range",
                message=(
                    f"{call}(..., {attribute}={value}) on bus {node.bus!r} is outside the QDAC-II's range: the "  # type: ignore[attr-defined]
                    f"{attribute} must be from {minimum:g} s to {maximum:g} s."
                ),
                node=node,  # type: ignore[arg-type]
            )


QILILAB_QBLOX_PARITY_V1_PROFILE = Profile(
    name="qililab-qblox-parity-v1",
    version=(1, 0, 0),
    extends=None,
    capabilities=_BLOCKS | _EXPRESSIONS | {"vendor.qililab.disable_autosync"},
    limits={},
    predicates=(),
)
"""Platform-level half: the blocks, sweeps and expressions qililab runs, all in real time, and the compiler setting
``qililab.disable_autosync``."""

QILILAB_HOST_PARITY_V1_PROFILE = Profile(
    name="qililab-host-parity-v1",
    version=(1, 0, 0),
    extends=None,
    capabilities=frozenset({"block.block", "vendor.qililab.disable_autosync"}),
    limits={},
    predicates=(),
)
"""Platform-level PC half: only plain blocks, so that one can group QDAC operations, which run on the PC, and the
compiler setting ``qililab.disable_autosync``, which runs nowhere, so it never decides where the body runs. Loops,
averages and ``if_trigger`` stay real-time only."""

QILILAB_QBLOX_BUS_PARITY_V1_PROFILE = Profile(
    name="qililab-qblox-bus-parity-v1",
    version=(1, 0, 0),
    extends=None,
    capabilities=_QBLOX_OPERATIONS | _QILILAB_WAVEFORMS | {"waveform.single", "waveform.iq"},
    limits={},
    predicates=(_reject_variable_in_waveform, _reject_unsupported_arithmetic),
)
"""Real-time half of a bus: the Qblox operations qililab compiles."""

QILILAB_QDAC_BUS_PARITY_V1_PROFILE = Profile(
    name="qililab-qdac-bus-parity-v1",
    version=(1, 0, 0),
    extends=None,
    capabilities=_QDAC_OPERATIONS
    | (_QILILAB_WAVEFORMS - {"waveform.iq_drag", "waveform.iq_pair"})
    | {"waveform.single"},
    limits={},
    predicates=(_reject_variable_in_waveform, *resolve_profile("qdac-default-v1").predicates),
)
"""PC half of a bus: the QDAC operations qililab sets up before the run, with qprogram-qdac's own checks."""

for _profile in (
    QILILAB_QBLOX_PARITY_V1_PROFILE,
    QILILAB_HOST_PARITY_V1_PROFILE,
    QILILAB_QBLOX_BUS_PARITY_V1_PROFILE,
    QILILAB_QDAC_BUS_PARITY_V1_PROFILE,
):
    register_profile(_profile)

QILILAB_QBLOX_PARITY_V1 = PlatformCapabilities(
    bus={},
    platform=BusCapabilities(
        rt=CompilerCapabilities.from_profile("qililab-qblox-parity-v1"),
        host=CompilerCapabilities.from_profile("qililab-host-parity-v1"),
    ),
    default_bus_profile=BusCapabilities(
        rt=CompilerCapabilities.from_profile("qililab-qblox-bus-parity-v1"),
        host=CompilerCapabilities.from_profile(
            "qililab-qdac-bus-parity-v1", extra_predicates=(_reject_qdac_time_out_of_range,)
        ),
    ),
)
"""What a qililab platform runs, passed to ``qprogram.validate``. Buses are plain names, so they all share one slot.
The QDAC half of a bus also checks the QDAC-II's range of a play delay and a trigger width."""
