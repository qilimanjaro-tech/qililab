"""BusElement class"""
from qililab.constants import RUNCARD
from qililab.settings import DDBBElement
from qililab.typings.factory_element import FactoryElement


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: DDBBElement

    def to_dict(self):
        """Return a dict representation of the BusElement class."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()

    def short_dict(self):
        """Return a dict representation of the BusElement class discarding all static elements."""
        return {
            key: value
            for key, value in self.to_dict().items()
            if key not in [RUNCARD.NAME, RUNCARD.ID, RUNCARD.CATEGORY, RUNCARD.FIRMWARE]
        }
