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
"""Registers the operations and blocks qililab adds to qprogram, under the ``qililab`` vendor.

A ``.qp`` file using any of them writes them as ``qililab.<name>`` and starts with
``require qililab <QP_FORMAT_VERSION>``. Importing this module is what makes qprogram able to read such a file, and
qprogram imports it by itself through the ``qprogram.vendors`` entry point when it meets that line.
"""

from typing import Protocol

import qprogram_qblox  # noqa: F401  (registers the qblox vendor first)
import qprogram_qdac  # noqa: F401  (registers the qdac vendor first)
from qprogram import ParseError
from qprogram.protocol import register_capability_tokens
from qprogram.serialization._specs import make_measurement_op_parse, measurement_op_serialize
from qprogram.serialization.registry import register_vendor_block, register_vendor_operation, register_vendor_version

from qililab.qprogram.blocks import IfTrigger, InfiniteLoop
from qililab.qprogram.operations.disable_autosync import DisableAutosync
from qililab.qprogram.operations.measure_reset import MeasureReset
from qililab.qprogram.operations.play import QbloxPlay

QP_FORMAT_VERSION = "0.1"
"""Format version of qililab's operations and blocks in a ``.qp`` file, written as ``require qililab 0.1``.

It is not qililab's version: bump it, with a migration, only in the change that alters how one of them is written.
"""

register_capability_tokens(
    "vendor.qililab.disable_autosync",
    "vendor.qililab.infinite_loop",
    "vendor.qililab.if_trigger",
    "vendor.qililab.measure_reset",
    "vendor.qililab.qblox_play",
)
register_vendor_version("qililab", QP_FORMAT_VERSION)
register_vendor_operation(
    "qililab",
    "measure_reset",
    MeasureReset,
    serialize=measurement_op_serialize,
    parse=make_measurement_op_parse(MeasureReset),
)
register_vendor_operation("qililab", "qblox_play", QbloxPlay)
register_vendor_operation("qililab", "disable_autosync", DisableAutosync)
_IF_TRIGGER_PARAMETERS = ("trigger_padding_ns", "expected_wait_time_ns")


class _HeaderParser(Protocol):
    """What a block header parser needs from qprogram's ``.qp`` parser: building the error it raises."""

    def parse_error(self, message: str) -> ParseError:
        """Return the error to raise for ``message``, pointing at the line being parsed."""


def _serialize_if_trigger_header(block: IfTrigger, ctx: object) -> str:
    """Write the header of an ``if_trigger`` block, with the parameters it was given: ``qililab.if_trigger key=value``.

    Args:
        block (IfTrigger): The block.
        ctx (object): The writer, unused: the parameters are plain integers.

    Returns:
        str: The header, without its trailing colon.
    """
    given = [f"{name}={getattr(block, name)}" for name in _IF_TRIGGER_PARAMETERS if getattr(block, name) is not None]
    return " ".join(["qililab.if_trigger", *given])


def _parse_if_trigger_header(tokens: list[str], ctx: _HeaderParser) -> IfTrigger:
    """Read the header of an ``if_trigger`` block: its ``key=value`` parameters.

    Args:
        tokens (list[str]): The tokens after the keyword.
        ctx (_HeaderParser): The parser, which builds the error.

    Returns:
        IfTrigger: The block, with an empty body.

    Raises:
        ParseError: If a token is not one of the block's parameters set to an integer.
    """
    parameters: dict[str, int] = {}
    for token in tokens:
        name, _, value = token.partition("=")
        if name not in _IF_TRIGGER_PARAMETERS or not value.lstrip("-").isdigit():
            raise ctx.parse_error(
                f"qililab.if_trigger takes {' and '.join(_IF_TRIGGER_PARAMETERS)} as integers, got {token!r}"
            )
        parameters[name] = int(value)
    return IfTrigger(**parameters)


register_vendor_block("qililab", "infinite_loop", InfiniteLoop)
register_vendor_block(
    "qililab",
    "if_trigger",
    IfTrigger,
    serialize_header=_serialize_if_trigger_header,
    parse_header=_parse_if_trigger_header,
)
