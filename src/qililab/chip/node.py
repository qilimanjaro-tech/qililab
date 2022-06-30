"""Node class"""
from dataclasses import dataclass
from typing import List

from qililab.typings import FactoryElement


@dataclass
class Node(FactoryElement):
    """Class representing a node of the chip's graph."""

    id_: int
    nodes: List[int]
