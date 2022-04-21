from dataclasses import dataclass
from typing import Dict, List

from qililab.settings.settings import Settings


@dataclass
class SchemaSettings(Settings):
    """Schema settings.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator", "mixer" and "schema".
        buses (List[List[Settings]]): List containing the settings of the elements for each bus.
    """

    buses: List[List[Settings]]

    def __post_init__(self):
        """Cast the settings of each element to the Settings class."""
        super().__post_init__()
        buses = []
        for bus in self.buses:
            bus_list = []
            for settings in bus:
                bus_list.append(Settings(**settings))
            buses.append(bus_list)
        self.buses = buses
