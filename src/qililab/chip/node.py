"""Node class"""
from dataclasses import dataclass

from qililab.settings import AliasElement
from qililab.typings import FactoryElement


@dataclass(kw_only=True)
class Node(AliasElement, FactoryElement):
    """Class representing a node of the chip's graph."""

    nodes: list[str]

    def __str__(self):
        """String representation of a node."""
        return f"{self.alias}"
