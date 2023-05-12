"""Buses class."""
from dataclasses import dataclass

from qililab.platform.components.bus import Bus
from qililab.system_control import ReadoutSystemControl, SimulatedSystemControl


@dataclass
class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (list[Bus]): List of Bus objects.
    """

    elements: list[Bus]

    def add(self, bus: Bus):
        """Add a bus to the list of buses.

        Args:
            bus (Bus): Bus object to append."""
        self.elements.append(bus)

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over buses."""
        return self.elements.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.elements.__getitem__(key)

    def __len__(self):
        """Redirect __len__ magic method."""
        return len(self.elements)

    def to_dict(self) -> list[dict]:
        """Return a dict representation of the Buses class."""
        return [bus.to_dict() for bus in self.elements]

    @property
    def readout_buses(self) -> list[Bus]:
        """Returns a list of buses containing system controls used for readout."""
        readout_sc = (ReadoutSystemControl, SimulatedSystemControl)
        return [bus for bus in self.elements if isinstance(bus.system_control, readout_sc)]
