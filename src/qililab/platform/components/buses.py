from dataclasses import InitVar
from typing import List

from qililab.platform.components.bus_control import BusControl
from qililab.platform.components.bus_readout import BusReadout
from qililab.typings import YAMLNames
from qililab.utils import nested_dataclass


@nested_dataclass
class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (List[Bus]): List of Bus objects.
    """

    elements: InitVar[List[dict]]

    def __post_init__(self, elements: List[dict]):
        """Cast each list element to its corresponding bus class."""
        self.buses: List[BusControl | BusReadout] = []
        for bus in elements:
            if bus[YAMLNames.READOUT.value] is True:
                self.buses.append(BusControl(**bus))
            elif bus[YAMLNames.READOUT.value] is False:
                self.buses.append(BusReadout(**bus))
            else:
                raise ValueError("Bus 'readout' key should contain a boolean.")

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
