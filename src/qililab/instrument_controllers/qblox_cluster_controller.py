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
from qililab.instruments import QbloxModule
from qililab.runcard.runcard_instrument_controllers import (
    QbloxClusterRuncardInstrumentController,
    RuncardInstrumentController,
)
from qililab.settings.instrument_controllers import QbloxClusterControllerSettings
from qililab.typings.instruments import QbloxClusterDevice


@InstrumentControllerFactory.register(InstrumentControllerType.QDEVIL_QDAC2_CONTROLLER)
class QbloxClusterController(InstrumentController2[QbloxClusterDevice, QbloxClusterControllerSettings, QbloxModule]):
    @classmethod
    def get_default_settings(cls) -> QbloxClusterControllerSettings:
        return QbloxClusterControllerSettings(alias="qblox_cluster_controller")

    def initial_setup(self):
        """Initial setup of the Qblox Cluster Controller."""
        self.device.reference_source(self.settings.reference_clock.value)
        super().initial_setup()

    def reset(self):
        """Reset the device and clear cache of all modules."""
        self.device.reset()
        for module in self.modules:
            module.clear_cache()

    def _initialize_device(self):
        self.device = QbloxClusterDevice(name=f"{self.settings.alias}", identifier=self.settings.connection.address)

    def _set_device_to_all_modules(self):
        for index, module in enumerate(self.settings.modules):
            self.modules[index].device = self.device.modules[module.slot - 1]

    def to_runcard(self) -> RuncardInstrumentController:
        return QbloxClusterRuncardInstrumentController(settings=self.settings)
