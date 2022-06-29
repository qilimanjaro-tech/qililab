"""Chip class."""
from dataclasses import dataclass
from typing import List

from qililab.chip.node import Node
from qililab.chip.qubit import Qubit
from qililab.chip.resonator import Resonator
from qililab.constants import YAML
from qililab.typings import Category
from qililab.utils import Factory


@dataclass
class Chip:
    """Chip representation as a graph."""

    id_: int
    category: Category
    ports: List[int]
    nodes: List[Node]

    def __post_init__(self):
        self.nodes = [Factory.get(name=node.pop(YAML.NAME))(**node) for node in self.nodes]

    def _find_qubit(self, idx: int) -> Qubit:
        """Find qubit from given idx value.

        Args:
            idx (int): Qubit index.

        Raises:
            ValueError: If no qubit is found.

        Returns:
            Qubit: Qubit node object.
        """
        for node in self.nodes:
            if isinstance(node, Qubit) and node.idx == idx:
                return node
        raise ValueError(f"Could not find qubit with idx {idx}.")

    def _get_adjacent_nodes(self, node: Node) -> List[Node]:
        """Get adjacent nodes from given node.

        Args:
            node (Node): Node object.

        Returns:
            List[Node]: List containing all adjacent nodes.
        """
        return [self.nodes[node_idx] for node_idx in node.nodes]

    def get_port_from_qubit_idx(self, idx: int, readout: bool) -> int:
        """Get control/readout port number from qubit index.

        Args:
            idx (int): Qubit index.
            readout (bool): Readout (True) or control (False) port.

        Raises:
            ValueError: If qubit doesn't have a control/readout port.

        Returns:
            int: Control/readout port.
        """
        qubit = self._find_qubit(idx=idx)
        if not readout:
            if qubit.port is None:
                raise ValueError(f"Qubit with index {idx} doesn't have a control line.")
            return qubit.port
        adj_nodes = self._get_adjacent_nodes(node=qubit)
        for node in adj_nodes:
            if isinstance(node, Resonator):
                return node.port
        raise ValueError(f"Qubit with index {idx} doesn't have a readout line.")
