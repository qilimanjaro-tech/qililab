from typing import List

from qibo.abstractions.gates import Gate
from qibo.core.circuit import Circuit as QiboCircuit


class Circuit(QiboCircuit):
    """Circuit class."""

    queue: List[Gate]
