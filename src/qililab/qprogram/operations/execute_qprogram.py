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
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from qililab.yaml import yaml

from . import Operation

if TYPE_CHECKING:
    from qililab.core import Variable
    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.qprogram import QProgram


@yaml.register_class
class ExecuteQProgram(Operation):
    def __init__(
        self,
        qprogram: QProgram | Callable[..., QProgram],  # type: ignore[misc]
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        debug: bool = False,
    ) -> None:
        super().__init__()
        self.qprogram: QProgram | Callable[[Variable, ...], QProgram] = qprogram  # type: ignore[misc]
        self.bus_mapping: dict[str, str] | None = bus_mapping
        self.calibration: Calibration | None = calibration
        self.debug: bool = debug
