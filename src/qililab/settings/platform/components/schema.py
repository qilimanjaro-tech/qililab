from dataclasses import dataclass
from typing import List

from qililab.settings.platform.components.bus import BusSettings
from qililab.settings.settings import Settings


@dataclass
class SchemaSettings(Settings):
    """Schema settings.

    Args:
        buses (BusesSettings): List containing the settings of the elements for each bus.
    """

    buses: List[BusSettings]

    def __post_init__(self):
        """Cast the settings of each element to the Settings class."""
        super().__post_init__()
        self.buses = [BusSettings(**bus_settings) for bus_settings in self.buses]

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return {
            "id_": self.id_,
            "name": self.name,
            "category": self.category.value,
            "buses": [bus.to_dict() for bus in self.buses],
        }
