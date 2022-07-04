"""Qubit class"""
from dataclasses import dataclass

from qililab.chip.node import Node
from qililab.typings import NodeName
from qililab.utils import Factory


@Factory.register
@dataclass
class Qubit(Node):
    """Qubit class"""

    name = NodeName.QUBIT
    frequency: float
    qubit_idx: int
