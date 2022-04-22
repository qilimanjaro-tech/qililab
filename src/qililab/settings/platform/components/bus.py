from dataclasses import asdict, dataclass
from typing import List

from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform.components.resonator import Resonator
from qililab.platform.utils.bus_element_hash_table import BusElementHashTable
from qililab.platform.utils.dict_factory import dict_factory
from qililab.settings.settings import Settings


@dataclass
class BusSettings(Settings):
    """Schema settings."""

    elements: List[QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator]

    def __post_init__(self):
        """Cast each element to its corresponding class."""
        super().__post_init__()
        self.elements = [BusElementHashTable.get(settings["name"])(settings) for settings in self.elements]

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over elements."""
        return self.elements.__iter__()

    def to_dict(self):
        """Return a dict representation of the BusSettings class"""
        return {
            "id_": self.id_,
            "name": self.name,
            "category": self.category.value,
            "elements": [asdict(element.settings, dict_factory=dict_factory) for element in self.elements],
        }
