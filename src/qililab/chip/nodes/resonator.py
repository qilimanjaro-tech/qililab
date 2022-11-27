"""Resonator class."""
from dataclasses import dataclass

from qililab.chip.node import Node
from qililab.typings import NodeName
from qililab.utils import Factory


@Factory.register
@dataclass(kw_only=True)
class Resonator(Node):
    """Resonator class"""

    name = NodeName.RESONATOR
    frequency: float
