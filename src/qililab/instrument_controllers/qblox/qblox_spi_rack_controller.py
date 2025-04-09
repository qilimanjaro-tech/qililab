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
from qililab.instruments.qblox.qblox_d5a import QbloxD5A
from qililab.instruments.qblox.qblox_s4g import QbloxS4G
from qililab.runcard.runcard_instrument_controllers import (
    QbloxSPIRackRuncardInstrumentController,
    RuncardInstrumentController,
)
from qililab.settings.instrument_controllers import ConnectionSettings, ConnectionType, QbloxSPIRackControllerSettings
from qililab.typings.instruments import QbloxSPIRackDevice


@InstrumentControllerFactory.register(InstrumentControllerType.QBLOX_SPI_RACK_CONTROLLER)
class QbloxSPIRackController(
    InstrumentController[QbloxSPIRackDevice, QbloxSPIRackControllerSettings, QbloxD5A | QbloxS4G]
):
    @classmethod
    def get_default_settings(cls) -> QbloxSPIRackControllerSettings:
        return QbloxSPIRackControllerSettings(
            alias="spi-rack", connection=ConnectionSettings(type=ConnectionType.USB, address="COM1")
        )

    def _initialize_device(self):
        self.device = QbloxSPIRackDevice(name=f"{self.alias}", address=self.settings.connection.address)

    def _set_device_to_all_modules(self):
        for module, instrument in zip(self.settings.modules, self.modules):
            module_type = "S4g" if isinstance(instrument, QbloxS4G) else "D5a"
            self.device.add_spi_module(address=module.slot, module_type=module_type)
            instrument.device = getattr(self.device, f"module{module.slot}")

    def to_runcard(self) -> RuncardInstrumentController:
        return QbloxSPIRackRuncardInstrumentController(settings=self.settings)
