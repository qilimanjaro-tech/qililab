"""Instruments class"""
from dataclasses import dataclass
from qililab.drivers.interfaces import BaseInstrument


@dataclass
class Instruments:
    """Instruments class."""

    elements: list[BaseInstrument]

    def get_instrument(self, alias: str | None = None):
        """Get element given an alias."""
        return next((element for element in self.elements if element.alias == alias), None)
