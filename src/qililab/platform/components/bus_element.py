"""BusElement class"""
from dataclasses import asdict

from qililab.constants import RUNCARD
from qililab.settings import AliasElement
from qililab.typings.factory_element import FactoryElement
from qililab.utils import dict_factory


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: AliasElement

    def to_dict(self):
        """Return a dict representation of the BusElement class."""
        return {RUNCARD.NAME: self.name.value} | asdict(self.settings, dict_factory=dict_factory)

    def short_dict(self):
        """Return a dict representation of the BusElement class discarding all static elements."""
        return {
            key: value
            for key, value in self.to_dict().items()
            if key not in [RUNCARD.NAME, RUNCARD.ID, RUNCARD.CATEGORY, RUNCARD.FIRMWARE]
        }
