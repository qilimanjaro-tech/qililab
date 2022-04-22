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
