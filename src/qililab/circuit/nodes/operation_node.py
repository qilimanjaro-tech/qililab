"""OperationNode class"""
from dataclasses import dataclass
from typing import Tuple

from qililab.circuit.nodes.node import Node
from qililab.circuit.operations import Operation


@dataclass
class OperationTiming:
    """Class to store timings of an operation"""

    start: int
    end: int


@dataclass
class OperationNode(Node):
    """Node representing an operation acting on one or more qubits

    Args:
        operation (Operation): The operation that is applied
        Node (Tuple[int]): The qubits the operation is applied on
        alias (str | None): An optional alias for easily retrieving the node (default = None)
    """

    operation: Operation
    qubits: Tuple[int, ...]
    alias: str | None = None
    timing: OperationTiming | None = None
