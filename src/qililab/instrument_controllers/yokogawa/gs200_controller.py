""" Yokogawa GS200 General Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.yokogawa.gs200 import GS200
from qililab.typings import YokogawaGS200
from qililab.typings.enums import InstrumentControllerName, InstrumentTypeName


@InstrumentControllerFactory.register
class GS200Controller(SingleInstrumentController):
    """YOKOGAWA GS200 class
    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (GS200): Instance of the qcodes GS200 class.
        settings (GS200Settings): Settings of the instrument.
    """

    name = InstrumentControllerName.YOKOGAWA_GS200

    @dataclass
    class GS200ControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific GS200 Controller."""

    settings: GS200ControllerSettings
    device: YokogawaGS200
    modules: Sequence[GS200]

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = YokogawaGS200(f"{self.name.value}", f"TCPIP0::{self.address}::inst0::INSTR")

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, GS200):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentTypeName.YOKOGAWA_GS200}"
                )
