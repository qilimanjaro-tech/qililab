"""Resonator class."""
from dataclasses import dataclass

from qililab.chip.node import Node
from qililab.typings import NodeName


@dataclass
class Resonator(Node):
    """Resonator class"""

    name = NodeName.RESONATOR
    frequency: float
    port: int
