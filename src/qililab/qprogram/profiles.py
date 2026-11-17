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
"""The capability profiles listing what qililab can run: ``qililab-qblox-parity-v1`` and ``qililab-experiment-parity-v1``.

qprogram can describe much more than qililab runs. Every QProgram is validated against
[`QILILAB_QBLOX_PARITY_V1`][qililab.qprogram.profiles.QILILAB_QBLOX_PARITY_V1] before compilation, and every Experiment
against [`QILILAB_EXPERIMENT_PARITY_V1`][qililab.qprogram.profiles.QILILAB_EXPERIMENT_PARITY_V1] before it runs, so
anything else fails there with qprogram's ``missing-capability`` (or one of the ``qililab.*`` codes below) instead of
running something wrong.

- A QProgram's loops sweep a ``Linspace`` only (``qp.for_loop``, ``from_linspace``), as qililab's ``for_loop`` did. No
  conditionals other than ``if_trigger``, no fragment calls, no ``set_parameter``/``get_parameter``, no
  ``qblox.set_acquisition_threshold``/``set_acquisition_rotation``. QDAC operations may sit inside loops.
- An Experiment's loops sweep values only (``for_loop``, ``loop``, ``from_values``), as qililab's Experiment did.
- Expressions are a variable, a constant, a negated variable, or one ``+`` or ``-`` between two of those.
- Waveforms are the ones qililab had, with no variable in their parameters.
"""

from collections.abc import Iterable, Iterator
from weakref import WeakKeyDictionary

import qprogram_qblox  # noqa: F401  (registers the qblox tokens)

# Importing qprogram_qdac also registers the qdac tokens and profile.
import qprogram_qdac  # noqa: F401
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
        "sweep.linspace",
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


# Per validate() run, whether each waveform already checked uses a variable, by id. A program plays the same waveform
# object many times: each waveform is only looked through once. The run's waveforms stay alive while it lasts, so their ids don't change.
_WAVEFORMS_WITH_VARIABLES: WeakKeyDictionary[ValidationContext, dict[int, bool]] = WeakKeyDictionary()


def _reject_variable_in_waveform(node: object, ctx: ValidationContext) -> Iterable[Diagnostic | DomainConstraint]:
    """Reject a waveform or weights whose parameters use a variable (e.g. a swept amplitude).

    qililab samples waveforms once, before the run, so it cannot follow a variable inside one.

    Args:
        node (object): The AST node being validated.
        ctx (ValidationContext): Program-wide facts, used only to keep the waveforms checked during this run.

    Yields:
        Diagnostic: A ``qililab.variable-in-waveform`` error when a waveform of ``node`` uses a variable.
    """
    attributes = getattr(node, "WAVEFORM_ATTRS", ())
    if not attributes:
        return
    checked = _WAVEFORMS_WITH_VARIABLES.setdefault(ctx, {})
    for attribute in attributes:
        waveform = getattr(node, attribute, None)
        if id(waveform) not in checked:
            checked[id(waveform)] = any(True for _ in _waveform_expressions(waveform))
        if checked[id(waveform)]:
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


QILILAB_QBLOX_PARITY_V1_PROFILE = Profile(
    name="qililab-qblox-parity-v1",
    version=(1, 0, 0),
    extends=None,
    capabilities=_BLOCKS | _EXPRESSIONS | {"vendor.qililab.disable_autosync"},
    limits={},
    predicates=(),
)
"""Platform level: the blocks, loops and expressions qililab runs, and the compiler setting
``qililab.disable_autosync``."""

QILILAB_BUS_PARITY_V1_PROFILE = Profile(
    name="qililab-bus-parity-v1",
    version=(1, 0, 0),
    extends=None,
    capabilities=_QBLOX_OPERATIONS | _QDAC_OPERATIONS | _QILILAB_WAVEFORMS | {"waveform.single", "waveform.iq"},
    limits={},
    predicates=(
        _reject_variable_in_waveform,
        _reject_unsupported_arithmetic,
        *resolve_profile("qdac-default-v1").predicates,
    ),
)
"""Bus level: the Qblox and QDAC operations qililab compiles, with qprogram-qdac's own checks. Which bus may carry
which operation is checked by the Qblox and QDAC pre-passes."""

QILILAB_EXPERIMENT_PARITY_V1_PROFILE = Profile(
    name="qililab-experiment-parity-v1",
    version=(1, 0, 0),
    extends=None,
    capabilities=frozenset(
        {"block.block", "block.average", "block.sweep", "block.parallel", "sweep.values", "sweep.arbitrary"}
    )
    | _EXPRESSIONS,
    limits={},
    predicates=(),
)
"""What an Experiment runs: blocks, averages and loops over values, which ``for_loop``, ``loop`` and ``from_values``
build."""

for _profile in (QILILAB_QBLOX_PARITY_V1_PROFILE, QILILAB_BUS_PARITY_V1_PROFILE, QILILAB_EXPERIMENT_PARITY_V1_PROFILE):
    register_profile(_profile)

QILILAB_QBLOX_PARITY_V1 = PlatformCapabilities(
    bus={},
    platform=BusCapabilities(rt=CompilerCapabilities.from_profile("qililab-qblox-parity-v1"), host=None),
    default_bus_profile=BusCapabilities(rt=CompilerCapabilities.from_profile("qililab-bus-parity-v1"), host=None),
)
"""What a qililab platform runs, passed to ``qprogram.validate``. Buses are plain names, so they all share one slot."""

QILILAB_EXPERIMENT_PARITY_V1 = PlatformCapabilities(
    bus={},
    platform=BusCapabilities(rt=CompilerCapabilities.from_profile("qililab-experiment-parity-v1"), host=None),
    default_bus_profile=BusCapabilities(
        rt=CompilerCapabilities.from_profile("qililab-experiment-parity-v1"), host=None
    ),
)
"""What an Experiment runs, passed to ``qprogram.validate`` by the experiment executor."""
