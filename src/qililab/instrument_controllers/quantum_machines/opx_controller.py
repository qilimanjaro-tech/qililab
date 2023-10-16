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

""" Quantum Machines OPX Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.typings import OPXDriver
from qililab.typings.enums import ConnectionName, InstrumentControllerName


@InstrumentControllerFactory.register
class OPXController(SingleInstrumentController):
    """Quantum Machines OPX class

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (OPXDriver): Instance of the qcodes Quantum Machines OPX class.
        settings (OPXControllerSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.OPX
    device: OPXDriver

    @dataclass
    class OPXControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Quantum Machines OPX Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: OPXControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = OPXDriver(
            name=f"{self.name.value}_{self.alias}", address=f"TCPIP0::{self.address}::INSTR", visalib="@py"
        )
