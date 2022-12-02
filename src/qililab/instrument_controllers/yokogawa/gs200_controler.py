from dataclasses import dataclass
from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentTypeName,
)
from qililab.instruments.yokogowa.gs200 import GS200
from qililab.typings import YokogawaGS200
from typing import Sequence

@InstrumentControllerFactory.register
class GS200Controller(SingleInstrumentController):
    """YOKOGAWA GS200 class

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (GS200): Instance of the qcodes GS200 class.
        settings (GS200Settings): Settings of the instrument.
    """

    name = InstrumentControllerName.YOKOGAWA
    device:YokogawaGS200
    modules: Sequence[GS200]

    @dataclass
    class GS200ControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific GS200 Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: GS200ControllerSettings
    
    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = YokogawaGS200(f"{self.name.value}_{self.id_}", f"TCPIP0::{self.address}::inst0::INSTR")

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, GS200):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentTypeName.YOKOGAWA_GS200}"
                )