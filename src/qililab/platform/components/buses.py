"""Buses class."""
from dataclasses import dataclass
from typing import List

from qililab.platform.components.bus_control import BusControl
from qililab.platform.components.bus_readout import BusReadout


@dataclass
class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (List[Bus]): List of Bus objects.
    """

    buses: List[BusControl | BusReadout]

    def add(self, bus: BusControl | BusReadout):
        """Add a bus to the list of buses.

        Args:
            bus (Bus): Bus object to append."""
        self.buses.append(bus)

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over buses."""
        return self.buses.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.buses.__getitem__(key)

    def __len__(self):
        """Redirect __len__ magic method."""
        return len(self.buses)
