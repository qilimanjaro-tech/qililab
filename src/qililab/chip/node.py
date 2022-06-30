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
