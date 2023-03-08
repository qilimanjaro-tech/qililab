from dataclasses import dataclass

from qililab.circuit.nodes.node import Node


@dataclass
class StartNode(Node):
    """Node representing the entry point of the circuit graph"""

    ...
