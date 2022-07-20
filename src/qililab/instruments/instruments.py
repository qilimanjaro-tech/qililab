"""Instruments class"""
from dataclasses import dataclass
from typing import List

import yaml

from qililab.instruments.instrument import Instrument
from qililab.typings.enums import Category


@dataclass
class Instruments:
    """Instruments class."""

    elements: List[Instrument]

    def get_instrument(self, alias: str | None = None, category: Category | None = None, id_: int | None = None):
        """Get element given an id_ and category"""
        if alias is not None:
            return next(
                (element for element in self.elements if element.settings.alias == alias),
                None,
            )
        return next(
            (element for element in self.elements if element.id_ == id_ and element.category == Category(category)),
            None,
        )

    def to_dict(self):
        """Return a dict representation of the Instruments class."""
        return [instrument.to_dict() for instrument in self.elements]

    def __str__(self) -> str:
        """
        Returns:
            str: String representation of the Instruments class.
        """
        return str(yaml.dump(self._short_dict(), sort_keys=False))

    def _short_dict(self):
        """Return a dict representation of the Instruments class discarding all static elements."""
        return [instrument.short_dict() for instrument in self.elements]
