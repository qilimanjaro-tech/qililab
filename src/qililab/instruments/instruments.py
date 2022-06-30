"""Instruments class"""
from dataclasses import dataclass
from typing import List

from qililab.instruments import Instrument
from qililab.typings import Category


@dataclass
class Instruments:
    """Instruments class."""

    elements: List[Instrument]

    def connect(self):
        """Connect to all instruments."""
        for instrument in self.elements:
            instrument.connect()

    def close(self):
        """Close all instruments."""
        for instrument in self.elements:
            instrument.close()

    def get_instrument(self, category: Category, id_: int):
        """Get element given an id_ and category"""
        return next(
            (element for element in self.elements if element.id_ == id_ and element.category == Category(category)),
            None,
        )

    def to_dict(self):
        """Return a dict representation of the Instruments class."""
        return [instrument.to_dict() for instrument in self.elements]
