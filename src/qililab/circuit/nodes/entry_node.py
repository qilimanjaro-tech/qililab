from dataclasses import dataclass

from qililab.circuit.nodes.node import Node


@dataclass
class EntryNode(Node):
    """Node representing the entry point of the circuit graph"""
