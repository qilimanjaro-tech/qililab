"""Node class"""
from dataclasses import dataclass

from qililab.settings import AliasElement
from qililab.typings import FactoryElement


@dataclass(kw_only=True)
class Node(AliasElement, FactoryElement):
    """Class representing a node of the chip's graph."""

    id_: int
    nodes: list[int]

    def __str__(self):
        """String representation of a node."""
        return f"{self.alias}" if self.alias is not None else f"{self.id_}"
