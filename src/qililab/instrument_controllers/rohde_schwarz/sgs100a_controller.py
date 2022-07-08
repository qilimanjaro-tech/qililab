""" Rohde & Schwarz SGS100A Instrument Controller """
from dataclasses import dataclass

from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.typings import RohdeSchwarzSGS100A
from qililab.typings.enums import ConnectionName, InstrumentControllerName


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

    @dataclass
    class SGS100AControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific SGS100A Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: SGS100AControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = RohdeSchwarzSGS100A(f"{self.name.value}_{self.id_}", f"TCPIP0::{self.address}::inst0::INSTR")
