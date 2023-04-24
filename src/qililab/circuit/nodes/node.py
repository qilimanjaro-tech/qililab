"""Node class"""
from abc import ABC
from dataclasses import dataclass, field


@dataclass
class Node(ABC):
    """Generic node of circuit graph"""

    index: int = field(init=False)
