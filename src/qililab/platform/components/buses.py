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

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over buses."""
        return self.buses.__iter__()
