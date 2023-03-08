from abc import ABC
from dataclasses import dataclass, field
from typing import Tuple

from qililab.circuit.operations import Operation


@dataclass
class Node(ABC):
    """Generic node of circuit graph"""

    index: int = field(init=False)
