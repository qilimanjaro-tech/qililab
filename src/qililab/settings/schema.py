from dataclasses import dataclass
from typing import List

from qililab.settings.settings import Settings


@dataclass
class SchemaSettings(Settings):
    """Schema settings.

    Args:
        buses (List[List[Settings]]): List containing the settings of the elements for each bus.
    """

    buses: List[List[Settings]]

    def __post_init__(self):
        """Cast the settings of each element to the Settings class."""
        super().__post_init__()
        buses = []
        for bus in self.buses:
            bus_list = [Settings(**settings) for settings in bus]
            buses.append(bus_list)
        self.buses = buses
