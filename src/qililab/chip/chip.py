"""Chip class."""
from dataclasses import asdict, dataclass
from typing import List

from qililab.chip.node import Node
from qililab.chip.nodes import Coil, Coupler, Port, Qubit, Resonator
from qililab.constants import RUNCARD
from qililab.settings.ddbb_element import DDBBElement
from qililab.typings import Category
from qililab.utils import Factory, dict_factory


@dataclass
class Chip(DDBBElement):
    """Chip representation as a graph."""

    nodes: List[Node]

    def __post_init__(self):
        """Cast nodes and category to their corresponding classes."""
        self.nodes = [Factory.get(name=node.pop(RUNCARD.NAME))(**node) for node in self.nodes]
        self.category = Category(self.category)

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
            if isinstance(node, Qubit) and node.qubit_index == idx:
                return node
        raise ValueError(f"Could not find qubit with idx {idx}.")

    def _get_adjacent_nodes(self, node: Node) -> List[Node]:
        """Get adjacent nodes from given node.

        Args:
            node (Node): Node object.

        Returns:
            List[Node]: List containing all adjacent nodes.
        """
        return [self.get_node_from_id(node_id=node_id) for node_id in node.nodes]

    def get_port_from_qubit_idx(self, idx: int, readout: bool) -> Port:
        """Get control/readout port number from qubit index.

        Args:
            idx (int): Qubit index.
            readout (bool): If True, return readout port and resonator frequency,
            if False return control port and qubit frequency.

        Raises:
            ValueError: If qubit doesn't have a control/readout port.

        Returns:
            int: Control/readout port.
        """
        qubit = self._find_qubit(idx=idx)
        if not readout:
            return self._get_adjacent_port(node=qubit)
        adj_nodes = self._get_adjacent_nodes(node=qubit)
        for node in adj_nodes:
            if isinstance(node, Resonator):
                return self._get_adjacent_port(node=node)
        raise ValueError(f"Qubit with index {idx} doesn't have a readout line.")

    def _get_adjacent_port(self, node: Node) -> Port:
        """Find node's port (if exists).

        Args:
            node (Node): Node class.

        Raises:
            ValueError: If no node is found.

        Returns:
            Port: Port class.
        """
        adj_nodes = self._get_adjacent_nodes(node)
        for adj_node in adj_nodes:
            if isinstance(adj_node, Port):
                return adj_node
        raise ValueError(f"Node with id {node.id_} is not connected to a port.")

    def get_port_nodes(self, port_id: int) -> List[Qubit | Resonator | Coupler | Coil]:
        """Get nodes connected to a given port.

        Args:
            port (Port): Port class.

        Returns:
            List[Node]: List of nodes connected to the given port.
        """
        port = self.get_node_from_id(node_id=port_id)
        return self._get_adjacent_nodes(node=port)  # type: ignore

    def get_node_from_id(self, node_id: int) -> Node:
        """Get node from given id.

        Args:
            node_id (int): Id of the node.

        Raises:
            ValueError: If no node is found.

        Returns:
            Node: Node class.
        """
        for node in self.nodes:
            if node.id_ == node_id:
                return node
        raise ValueError(f"Could not find node with id {node_id}.")

    def get_node_from_alias(self, alias: str):
        """Get node from given alias.

        Args:-

            ValueError: If no node is found.

        Returns:
            Node: Node class.
        """
        for node in self.nodes:
            if node.alias == alias:
                return node
        raise ValueError(f"Could not find node with alias {alias}")

    def get_qubit_idx_from_node(self, node: Node) -> int:
        """Get qubit id from given node.

        Args:
            node (Node): Node class.

        Returns:
            int: Qubit id.
        """
        adj_nodes = self._get_adjacent_nodes(node=node)
        for adj_node in adj_nodes:
            if isinstance(adj_node, Qubit):
                return adj_node.qubit_index
            if isinstance(adj_node, Resonator):
                return self.get_qubit_idx_from_node(node=adj_node)
        raise ValueError(f"Could not find qubit connected to node with id {node.id_}")

    def to_dict(self):
        """Return a dict representation of the Chip class."""
        return {
            "id_": self.id_,
            "category": self.category.value,
            "nodes": [{RUNCARD.NAME: node.name.value} | asdict(node, dict_factory=dict_factory) for node in self.nodes],
        }

    @property
    def num_qubits(self) -> int:
        """Chip 'num_qubits' property

        Returns:
            int: Number of qubits.
        """
        return sum(isinstance(node, Qubit) for node in self.nodes)

    @property
    def num_ports(self) -> int:
        """Chip 'num_ports' property

        Returns:
            int: Number of ports.
        """
        return sum(isinstance(node, Port) for node in self.nodes)

    def __str__(self):
        """String representation of the Chip class."""
        string = f"Chip {self.alias} with {self.num_qubits} qubits and {self.num_ports} ports: \n\n"
        for node in self.nodes:
            if isinstance(node, Port):
                adj_nodes = self._get_adjacent_nodes(node=node)
                string += f" * Port {node.id_}: ----"
                for adj_node in adj_nodes:
                    string += f"|{adj_node}|--"
                string += "--\n"
        return string
