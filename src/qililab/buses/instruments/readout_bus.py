"""Driver for the Readout Bus class."""
from qililab.buses.interfaces import Bus

class ReadoutBus(Bus):
    """Qililab's driver for Readout Bus"""

    def __init__(self, name: str, address: str | None = None, **kwargs):
        """Initialise the bus.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        pass
