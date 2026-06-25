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

"""The ``qililab`` vendor namespace for the new QProgram.

qililab wears two hats over the vendor-agnostic ``qprogram`` core: it is a *platform* (it implements
:class:`~qprogram.platform.PlatformProtocol` via :class:`~qililab.platform.Platform`) **and** a
*vendor* (it registers private operations that only qililab knows how to execute). This module is the
vendor hat.

The core ``qprogram`` package has no notion of crosstalk — crosstalk is a qililab-only concern. So
``set_crosstalk`` lives here, as ``program.qililab.set_crosstalk(matrix)``, carrying qililab's own
:class:`~qililab.qprogram.crosstalk_matrix.CrosstalkMatrix`. It is a bus-less, software-dispatched
orchestration op (like ``set_parameter`` / ``get_parameter``): the executor applies the flux-crosstalk
compensation host-side / at compile time before driving the hardware frontier.

Importing :mod:`qililab.qprogram.v2` registers this namespace (see :func:`register_qililab_vendor`),
so ``program.qililab.set_crosstalk(...)`` works on any QProgram instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from qprogram.operations.operation import Operation
from qprogram.protocol import register_capability_tokens
from qprogram.qprogram import QProgram as _BaseQProgram
from qprogram.serialization.registry import register_vendor_operation, register_vendor_version
from qprogram.vendor import VendorNamespace

if TYPE_CHECKING:
    from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix

#: The vendor name + its single capability token. ``set_crosstalk`` is bus-less and
#: software-dispatched, so the platform routes it to the platform slot's software half.
VENDOR_NAME = "qililab"
SET_CROSSTALK_TOKEN = "vendor.qililab.set_crosstalk"  # noqa: S105 - capability token, not a secret

#: qililab vendor protocol version (informational; mirrored into ``require qililab <x.y>``).
QILILAB_VENDOR_VERSION = "0.1.0"


class SetCrosstalk(Operation):
    """Install a flux-crosstalk matrix for the rest of the program (qililab vendor op).

    A bus-less, software-dispatched operation: it carries a
    :class:`~qililab.qprogram.crosstalk_matrix.CrosstalkMatrix` (linear or non-linear) that the
    qililab executor uses to compensate flux operations before they are compiled to hardware. It is
    not a real-time instruction — it configures how subsequent flux ops are lowered.

    Args:
        crosstalk: The crosstalk matrix (qililab's :class:`CrosstalkMatrix` /
            :class:`NonLinearCrosstalkMatrix`).
    """

    BUS_ATTRS: ClassVar[tuple[str, ...]] = ()

    def __init__(self, crosstalk: CrosstalkMatrix) -> None:
        self.crosstalk = crosstalk

    def required_capabilities(self) -> set[str]:
        return {SET_CROSSTALK_TOKEN}

    def variables(self) -> set:
        # The crosstalk matrix holds no QProgram Variables; override to avoid the base
        # introspection descending into the (non-AST) CrosstalkMatrix object.
        return set()


class QililabNamespace(VendorNamespace):
    """The ``qililab`` vendor namespace — private qililab operations on a QProgram.

    Accessed via ``program.qililab.<operation>()`` after registration.
    """

    def set_crosstalk(self, crosstalk: CrosstalkMatrix) -> None:
        """Install a flux-crosstalk matrix used to compensate subsequent flux operations.

        Args:
            crosstalk: A qililab :class:`~qililab.qprogram.crosstalk_matrix.CrosstalkMatrix` (or
                :class:`NonLinearCrosstalkMatrix`).
        """
        self._append(SetCrosstalk(crosstalk=crosstalk))


_REGISTERED = False


def register_qililab_vendor() -> None:
    """Register the ``qililab`` vendor namespace, version, operation, and capability token.

    Idempotent — safe to call on every import of :mod:`qililab.qprogram.v2`.
    """
    global _REGISTERED
    if _REGISTERED:
        return
    register_capability_tokens(SET_CROSSTALK_TOKEN)
    _BaseQProgram.register_vendor(VENDOR_NAME, QililabNamespace)
    register_vendor_version(VENDOR_NAME, QILILAB_VENDOR_VERSION)
    register_vendor_operation(VENDOR_NAME, "set_crosstalk", SetCrosstalk)
    _REGISTERED = True


__all__ = ["QililabNamespace", "SetCrosstalk", "register_qililab_vendor"]
