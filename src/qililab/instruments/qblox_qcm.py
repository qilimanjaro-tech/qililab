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

from typing import Any, Callable

from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox_module import QbloxControlModule
from qililab.runcard.runcard_instruments import QbloxQCMRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxLFOutputSettings, QbloxQCMSettings, QbloxSequencerSettings
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QBLOX_QCM)
class QbloxQCM(QbloxControlModule[QbloxQCMSettings]):
    @classmethod
    def get_default_settings(cls) -> QbloxQCMSettings:
        return QbloxQCMSettings(alias="qcm", channels=[QbloxSequencerSettings(id=index) for index in range(6)])

    def initial_setup(self):
        super().initial_setup()

        for output in self.settings.outputs:
            self._on_output_offset_changed(value=output.offset, output=output.port)

    def _on_output_offset_changed(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset,
            1: self.device.out1_offset,
            2: self.device.out2_offset,
            3: self.device.out3_offset,
        }
        operations[output](value)

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQCMRuncardInstrument(settings=self.settings)

    def is_awg(self) -> bool:
        return True
