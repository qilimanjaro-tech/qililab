from dataclasses import dataclass
from typing import List

from qililab.platform.components.bus_control import BusControl
from qililab.platform.components.bus_readout import BusReadout
from qililab.typings import BusTypes, YAMLNames


@dataclass
class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (List[Bus]): List of Bus objects.
    """

    buses: List[BusControl | BusReadout]

    def __post_init__(self):
        """Cast each list element to its corresponding bus class."""
        for bus_idx, bus in enumerate(self.buses):
            if bus[YAMLNames.NAME.value] == BusTypes.BUS_CONTROL.value:
                self.buses[bus_idx] = BusControl(bus)
            elif bus[YAMLNames.NAME.value] == BusTypes.BUS_READOUT.value:
                self.buses[bus_idx] = BusReadout(bus)
            else:
                raise ValueError(
                    f"Bus name should be either {BusTypes.BUS_CONTROL.value} or {BusTypes.BUS_READOUT.value}"
                )

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
