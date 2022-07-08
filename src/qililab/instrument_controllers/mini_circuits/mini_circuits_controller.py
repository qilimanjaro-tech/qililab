""" MiniCircuits Instrument Controller """
from dataclasses import dataclass

from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.typings import MiniCircuitsDriver
from qililab.typings.enums import ConnectionName, InstrumentControllerName


@InstrumentControllerFactory.register
class MiniCircuitsController(SingleInstrumentController):
    """MiniCircuits class

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (MiniCircuitsDriver): Instance of the qcodes MiniCircuits class.
        settings (MiniCircuitsSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.MINI_CIRCUITS
    device: MiniCircuitsDriver

    @dataclass
    class MiniCircuitsControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific MiniCircuits Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: MiniCircuitsControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = MiniCircuitsDriver(
            name=f"{self.name.value}_{self.id_}",
            address=self.address,
        )
