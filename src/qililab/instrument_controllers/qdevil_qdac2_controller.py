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

from qililab.instrument_controllers.instrument_controller import InstrumentController
from qililab.instrument_controllers.instrument_controller_factory import InstrumentControllerFactory
from qililab.instrument_controllers.instrument_controller_type import InstrumentControllerType
from qililab.instruments.qdevil_qdac2 import QDevilQDAC2
from qililab.runcard.runcard_instrument_controllers import (
    QDevilQDAC2RuncardInstrumentController,
    RuncardInstrumentController,
)
from qililab.settings.instrument_controllers import ConnectionType, QDevilQDAC2ControllerSettings
from qililab.typings.instruments import QDevilQDAC2Device


@InstrumentControllerFactory.register(InstrumentControllerType.QDEVIL_QDAC2_CONTROLLER)
class QDevilQDAC2Controller(InstrumentController[QDevilQDAC2Device, QDevilQDAC2ControllerSettings, QDevilQDAC2]):
    @classmethod
    def get_default_settings(cls) -> QDevilQDAC2ControllerSettings:
        return QDevilQDAC2ControllerSettings(alias="qdac2_controller")

    def _initialize_device(self):
        if self.settings.connection.type == ConnectionType.TCP_IP:
            self.device = QDevilQDAC2Device(f"{self.name.value}", f"TCPIP::{self.address}::5025::SOCKET")
        else:
            self.device = QDevilQDAC2Device(f"{self.name.value}", f"ASRL/dev/{self.address}::INSTR")

    def _set_device_to_all_modules(self):
        self.modules[0].device = self.device

    def to_runcard(self) -> RuncardInstrumentController:
        return QDevilQDAC2RuncardInstrumentController(settings=self.settings)
