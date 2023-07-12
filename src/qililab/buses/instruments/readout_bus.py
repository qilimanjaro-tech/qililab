"""Driver for the Readout Bus class."""
from qililab.buses.instruments.bus import GenericBus
from qililab.buses.interfaces import BusInterface

class ReadoutBus(GenericBus, BusInterface):
    """Qililab's driver for Readout Bus"""

    def __init__(self, name: str, address: str | None = None, **kwargs):
        """Initialise the bus.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        super().__init__()
