"""Node class"""
from dataclasses import dataclass

from qililab.settings import Settings
from qililab.typings import FactoryElement


@dataclass(kw_only=True)
class Node(Settings, FactoryElement):
    """Class representing a node of the chip's graph."""

    alias: str
    nodes: list[str]

    def __str__(self):
        """String representation of a node."""
        return f"{self.alias}"
