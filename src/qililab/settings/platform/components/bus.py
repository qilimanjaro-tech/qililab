from dataclasses import dataclass
from typing import List

from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform.components.resonator import Resonator
from qililab.platform.utils.bus_element_hash_table import BusElementHashTable
from qililab.settings.settings import Settings


@dataclass
class BusSettings(Settings):
    """Schema settings."""

    elements: List[QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator]

    def __post_init__(self):
        """Cast each element to its corresponding class."""
        self.elements = [BusElementHashTable.get(settings["name"])(settings) for settings in self.elements]
