from dataclasses import dataclass, field
from typing import Dict, List

from qililab.platform.components.bus import Bus


@dataclass
class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (List[Bus]): List of Bus objects.
    """

    buses: List[Bus] = field(default_factory=list)

    def append(self, bus: Bus):
        """Append a bus to the list of buses.

        Args:
            bus (Bus): Bus object to append."""
        self.buses.append(bus)

    def to_dict(self) -> List[List[Dict]]:
        """Return all Buses information as a dictionary."""
        return [bus.to_dict() for bus in self.buses]
