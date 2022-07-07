""" Keithley2600 Instrument Controller """
from dataclasses import dataclass

from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.typings import Keithley2600Driver
from qililab.typings.enums import ConnectionName, InstrumentControllerName


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

    @dataclass
    class Keithley2600ControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific Keithley2600 Controller."""

        def __post_init__(self):
            self.connection.name = ConnectionName.TCP_IP

    settings: Keithley2600ControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = Keithley2600Driver(
            name=f"{self.name.value}_{self.id_}", address=f"TCPIP0::{self.address}::INSTR", visalib="@py"
        )
