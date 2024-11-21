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

from qililab.instrument_controllers.instrument_controller2 import InstrumentController2
from qililab.instrument_controllers.instrument_controller_factory import InstrumentControllerFactory
from qililab.instrument_controllers.instrument_controller_type import InstrumentControllerType
from qililab.instruments.rohde_schwarz_sg100 import RohdeSchwarzSG100
from qililab.runcard.runcard_instrument_controllers import RohdeSchwarzSG100RuncardInstrumentController
from qililab.settings.instrument_controllers import ConnectionSettings, RohdeSchwarzSG100ControllerSettings
from qililab.typings.instruments import RohdeSchwarzSGS100ADevice


@InstrumentControllerFactory.register(InstrumentControllerType.ROHDE_SCHWARZ_SG100_CONTROLLER)
class RohdeSchwarzSGS100AController(
    InstrumentController2[
        RohdeSchwarzSGS100ADevice,
        RohdeSchwarzSG100ControllerSettings,
        RohdeSchwarzSG100RuncardInstrumentController,
        RohdeSchwarzSG100,
    ]
):
    @classmethod
    def get_default_settings(cls) -> RohdeSchwarzSG100ControllerSettings:
        return RohdeSchwarzSG100ControllerSettings(
            alias="qdac2_controller", connection=ConnectionSettings(), reference_clock="internal"
        )

    def _initialize_device(self):
        self.device = RohdeSchwarzSGS100ADevice(
            f"{self.name.value}_{self.alias}", f"TCPIP0::{self.address}::inst0::INSTR"
        )

    def _set_device_to_all_modules(self):
        self.modules[0].device = self.device

    def to_runcard(self) -> RohdeSchwarzSG100RuncardInstrumentController:
        return RohdeSchwarzSG100RuncardInstrumentController(settings=self.settings)
