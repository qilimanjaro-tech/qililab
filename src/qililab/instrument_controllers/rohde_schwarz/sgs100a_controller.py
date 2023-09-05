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

""" Rohde & Schwarz SGS100A Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.rohde_schwarz.sgs100a import SGS100A
from qililab.typings import RohdeSchwarzSGS100A
from qililab.typings.enums import ConnectionName, InstrumentControllerName, InstrumentTypeName, Parameter


@InstrumentControllerFactory.register
class SGS100AController(SingleInstrumentController):
    """Rohde & Schwarz SGS100A class

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    name = InstrumentControllerName.ROHDE_SCHWARZ
    device: RohdeSchwarzSGS100A
    modules: Sequence[SGS100A]

    @dataclass
    class SGS100AControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific SGS100A Controller."""

        reference_clock: str

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: SGS100AControllerSettings

    @SingleInstrumentController.CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        self.device.ref_osc_source(self.settings.reference_clock)
        super().initial_setup()

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = RohdeSchwarzSGS100A(f"{self.name.value}_{self.alias}", f"TCPIP0::{self.address}::inst0::INSTR")

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, SGS100A):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentTypeName.ROHDE_SCHWARZ}"
                )

    def to_dict(self):
        """Return a dict representation of the SGS100A controller class."""
        return super().to_dict() | {
            Parameter.REFERENCE_CLOCK.value: self.settings.reference_clock,
        }
