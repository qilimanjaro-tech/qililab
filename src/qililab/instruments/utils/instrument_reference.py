""" Instrument Reference class. """

from dataclasses import dataclass

from qililab.constants import INSTRUMENTREFERENCE
from qililab.typings.enums import Category


@dataclass
class InstrumentReference:
    """References an Instrument with its category and alias to be retrieved from
        the Instrument Factory.

    Args:
        category (Category): The category of the Instrument.
        alias (str): The alias name of the Instrument.
        slot_id (int): The number that identifies the slot used by the instrument within the
                            the possible list of available modules (i.e. on a Cluster).
    """

    category: Category
    alias: str
    slot_id: int  # slot_id represents the number displayed in the cluster

    def __iter__(self):
        """Iterate over InstrumentReference elements.

        Yields:
            Tuple[Tuple[str, Category], Tuple[str, int], Tuple[str, int]]: category, alias and slot_id
        """
        yield from self.__dict__.items()

    def to_dict(self):
        """Return a dict representation of the InstrumentReference class."""
        return {self.category.value: self.alias, INSTRUMENTREFERENCE.SLOT_ID: self.slot_id}

    @classmethod
    def from_dict(cls, settings: dict):
        """Build an InstrumentReference from a settings dictionary

        Args:
            settings (dict): an instrument reference from the settings file
        """
        for name, value in settings.items():
            if name == INSTRUMENTREFERENCE.SLOT_ID:
                slot_id = value
                continue
            if Category(name):
                category = name
                alias = value
                continue
        return InstrumentReference(category=Category(category), alias=alias, slot_id=slot_id)
