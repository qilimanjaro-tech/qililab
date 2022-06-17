"""Instruments class"""
from dataclasses import dataclass
from typing import List

from qililab.instruments import Instrument
from qililab.typings import Category


@dataclass
class Instruments:
    """Instruments class."""

    elements: List[Instrument]

    def get(self, settings: dict):
        """Get element given an id_ and category"""
        id_ = settings.get("id_")
        category = settings.get("category")
        if not isinstance(id_, int):
            raise ValueError("Invalid value for id.")
        if not isinstance(category, str):
            raise ValueError("Invalid value for category.")
        return next(
            (element for element in self.elements if element.id_ == id_ and element.category == Category(category)),
            None,
        )
