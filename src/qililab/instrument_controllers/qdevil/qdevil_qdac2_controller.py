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

"""QDevil QDAC-II Controller"""
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.typings import QDevilQDac2 as QDevilQDac2Device
from qililab.typings.enums import ConnectionName, InstrumentControllerName, InstrumentTypeName


@InstrumentControllerFactory.register
class QDevilQDac2Controller(SingleInstrumentController):
    """QDevil QDAC-II controller class
    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (QDevilQDac2Device): Instance of the QDevil QDAC-II class.
        settings (QDevilQDac2ControllerSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.QDEVIL_QDAC2

    @dataclass
    class QDevilQDac2ControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific GS200 Controller."""

    settings: QDevilQDac2ControllerSettings
    device: QDevilQDac2Device
    modules: Sequence[QDevilQDac2]

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        if self.settings.connection.name == ConnectionName.TCP_IP:
            self.device = QDevilQDac2Device(f"{self.name.value}", f"TCPIP::{self.address}::5025::SOCKET")
        else:
            self.device = QDevilQDac2Device(f"{self.name.value}", f"ASRL/dev/{self.address}::INSTR")

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, QDevilQDac2):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentTypeName.QDEVIL_QDAC2}"
                )
