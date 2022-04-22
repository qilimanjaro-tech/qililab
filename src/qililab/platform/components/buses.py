from typing import Dict, List

from qililab.platform.components.bus import Bus
from qililab.settings.platform.components.bus import BusSettings


class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (List[Bus]): List of Bus objects.
    """

    def __init__(self, buses: List[BusSettings]):
        self.buses = [Bus(bus_settings) for bus_settings in buses]

    def append(self, bus: Bus):
        """Append a bus to the list of buses.

        Args:
            bus (Bus): Bus object to append."""
        self.buses.append(bus)

    def to_dict(self) -> List[List[Dict]]:
        """Return all Buses information as a dictionary."""
        return [bus.to_dict() for bus in self.buses]

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over buses."""
        return self.buses.__iter__()
