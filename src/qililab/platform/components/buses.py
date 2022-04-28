from typing import List

from qililab.platform.components.bus import Bus


class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (List[Bus]): List of Bus objects.
    """

    def __init__(self, buses: List[Bus.BusSettings]):
        self.buses = [Bus(bus_settings) for bus_settings in buses]

    def add(self, bus: Bus):
        """Add a bus to the list of buses.

        Args:
            bus (Bus): Bus object to append."""
        self.buses.append(bus)

    def connect(self):
        """Connect to the instruments."""
        for bus in self.buses:
            bus.connect()

    def setup(self):
        """Setup instruments with platform settings."""
        for bus in self.buses:
            bus.setup()

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over buses."""
        return self.buses.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.buses.__getitem__(key)
