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

""" Keithley2600 Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.keithley.keithley_2600 import Keithley2600
from qililab.typings import Keithley2600Driver
from qililab.typings.enums import ConnectionName, InstrumentControllerName, InstrumentTypeName


@InstrumentControllerFactory.register
class Keithley2600Controller(SingleInstrumentController):
    """Keithley2600 class

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (Keithley2600Driver): Instance of the qcodes Keithley2600 class.
        settings (Keithley2600Settings): Settings of the instrument.
    """

    name = InstrumentControllerName.KEITHLEY2600
    device: Keithley2600Driver
    modules: Sequence[Keithley2600]

    @dataclass
    class Keithley2600ControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Keithley2600 Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: Keithley2600ControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = Keithley2600Driver(
            name=f"{self.name.value}_{self.alias}", address=f"TCPIP0::{self.address}::INSTR", visalib="@py"
        )

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, Keithley2600):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentTypeName.KEITHLEY2600}"
                )
