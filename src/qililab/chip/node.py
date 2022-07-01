"""Node class"""
from dataclasses import dataclass
from typing import List

from qililab.settings import DDBBElement
from qililab.typings import Category, FactoryElement


@dataclass(kw_only=True)
class Node(DDBBElement, FactoryElement):
    """Class representing a node of the chip's graph."""

    category: Category = Category.NODE
    nodes: List[int]

    def __str__(self):
        """String representation of a node."""
        return f"{self.alias}" if self.alias is not None else f"{self.category}_{self.id_}"
