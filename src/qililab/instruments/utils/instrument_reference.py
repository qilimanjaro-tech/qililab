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
    slot_id: int

    def __iter__(self):
        """Iterate over InstrumentReference elements.

        Yields:
            Tuple[str, str]: _description_
        """
        yield self.category.value, self.alias, self.slot_id

    def to_dict(self):
        """Return a dict representation of the InstrumentReference class."""
        return {self.category.value: self.alias, INSTRUMENTREFERENCE.SLOT_ID: self.slot_id}
