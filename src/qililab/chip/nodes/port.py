"""Port class."""
from dataclasses import dataclass

from qililab.chip.node import Node
from qililab.typings import NodeName
from qililab.typings.enums import Line
from qililab.utils import Factory


@Factory.register
@dataclass
class Port(Node):
    """Port class."""

    name = NodeName.PORT
    line: Line
