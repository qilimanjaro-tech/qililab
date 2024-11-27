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
import os

from qm.octave import QmOctaveConfig

from qililab.instrument_controllers.instrument_controller2 import InstrumentController2
from qililab.instrument_controllers.instrument_controller_factory import InstrumentControllerFactory
from qililab.instrument_controllers.instrument_controller_type import InstrumentControllerType
from qililab.instruments import QuantumMachinesOPX
from qililab.runcard.runcard_instrument_controllers import (
    QuantumMachinesClusterRuncardInstrumentController,
    RuncardInstrumentController,
)
from qililab.settings.instrument_controllers import QuantumMachinesClusterControllerSettings
from qililab.typings.instruments import QuantumMachinesDevice


@InstrumentControllerFactory.register(InstrumentControllerType.QUANTUM_MACHINES_CLUSTER_CONTROLLER)
class QDevilQDAC2Controller(
    InstrumentController2[QuantumMachinesDevice, QuantumMachinesClusterControllerSettings, QuantumMachinesOPX]
):
    @classmethod
    def get_default_settings(cls) -> QuantumMachinesClusterControllerSettings:
        return QuantumMachinesClusterControllerSettings(alias="quantum_machines_cluster", cluster="cluster")

    def _initialize_device(self):
        calibration_db_path = (
            self.settings.calibration_db_path if self.settings.calibration_db_path is not None else os.getcwd()
        )

        octave_config = QmOctaveConfig()
        octave_config.set_calibration_db(path=calibration_db_path)
        self.device = QuantumMachinesDevice(
            host=self.settings.connection.address, cluster_name=self.settings.cluster, octave=octave_config
        )

    def _set_device_to_all_modules(self):
        self.modules[0].device = self.device

    def to_runcard(self) -> RuncardInstrumentController:
        return QuantumMachinesClusterRuncardInstrumentController(settings=self.settings)
