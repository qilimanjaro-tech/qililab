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

"""KeySight E5080B Instrument Controller"""

from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.typings.enums import ConnectionName, InstrumentControllerName, InstrumentName
from qililab.typings.instruments.rswu_sp16tr import RSWUSP16TR


@InstrumentControllerFactory.register
class RSWUSP16TRController(SingleInstrumentController):
    """Becker RSWU-SP16TR Instrument Controller

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (RSWUSP16TR): Instance of the qcodes RSWUSP16TR class.
        settings (RSWUSP16TRSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.RSWU_SP16TR
    device: RSWUSP16TR

    modules: Sequence[RSWUSP16TR]

    @dataclass
    class RSWUSP16TRontrollerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific RSWU-SP16TR Controller."""

        # timeout: float = DEFAULT_TIMEOUT
        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: RSWUSP16TRontrollerSettings

    @SingleInstrumentController.CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        super().initial_setup()

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

        self.device = RSWUSP16TR(
            name=f"{self.name.value}_{self.alias}", address=f"TCPIP::{self.address}::INSTR", visalib="@py"
        )

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, RSWUSP16TR):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentName.KEYSIGHT_E5080B}"
                )
