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
"""The operation ``qp.qblox.disable_autosync = True`` adds to a program."""

from typing import ClassVar

from qprogram.operations import Operation


class DisableAutosync(Operation):
    """Tells the Qblox compiler not to sync every bus at the end of each loop and average.

    It is a setting of the whole program, kept at the top of its body so that a ``.qp`` file keeps it too: there it
    reads ``qililab.disable_autosync``. Set it with ``qp.qblox.disable_autosync = True`` rather than directly.
    """

    BUS_ATTRS: ClassVar[tuple[str, ...]] = ()

    def required_capabilities(self) -> set[str]:
        """Return ``vendor.qililab.disable_autosync``.

        Returns:
            set[str]: The capability tokens the operation needs.
        """
        return {"vendor.qililab.disable_autosync"}
