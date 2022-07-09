""" Keithley2600 Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.instruments.keithley.keithley_2600 import Keithley2600
from qililab.typings import Keithley2600Driver
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentTypeName,
)


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
    class Keithley2600ControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific Keithley2600 Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: Keithley2600ControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = Keithley2600Driver(
            name=f"{self.name.value}_{self.id_}", address=f"TCPIP0::{self.address}::INSTR", visalib="@py"
        )

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, Keithley2600):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentTypeName.KEITHLEY2600}"
                )
