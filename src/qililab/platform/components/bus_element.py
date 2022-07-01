"""BusElement class"""
from dataclasses import asdict
from enum import Enum
from typing import Dict, List

from qililab.constants import RUNCARD
from qililab.settings import DDBBElement
from qililab.typings.factory_element import FactoryElement


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: DDBBElement

    def to_dict(self):
        """Return a dict representation of the BusElement class."""
        return {RUNCARD.NAME: self.name.value} | asdict(self.settings, dict_factory=dict_factory)

    def short_dict(self):
        """Return a dict representation of the BusElement class discarding all static elements."""
        return {
            key: value
            for key, value in self.to_dict().items()
            if key not in [RUNCARD.NAME, RUNCARD.ID, RUNCARD.CATEGORY, RUNCARD.IP, RUNCARD.FIRMWARE]
        }


def dict_factory(data):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values
    and all BusElement objects with its corresponding settings dictionaries."""
    result: Dict[str, List[Dict[str, int | float | str]] | str | int | float] = {}
    for key, value in data:
        if isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
