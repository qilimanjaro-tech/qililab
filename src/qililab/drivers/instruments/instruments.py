"""Instruments class"""
from dataclasses import dataclass

import yaml

from qililab.drivers.interfaces import BaseInstrument


@dataclass
class Instruments:
    """Class used to represent a group of instruments."

    elements: list[BaseInstrument]

    def get_instrument(self, alias: str | None = None):
        """Get element given an alias."""
        return next((element for element in self.elements if element.alias == alias), None)

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
