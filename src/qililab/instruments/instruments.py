"""Instruments class"""
from dataclasses import dataclass
from typing import List

from qililab.instruments import Instrument
from qililab.typings import Category


@dataclass
class Instruments:
    """Instruments class."""

    elements: List[Instrument]

    def get(self, id_: int, category: Category):
        """Get element given an id_ and category"""
        return next((element for element in self.elements if element.id_ == id_ and element.category == category), None)
