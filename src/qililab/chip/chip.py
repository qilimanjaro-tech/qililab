"""Chip class."""
from dataclasses import asdict, dataclass

from qililab.chip.node import Node
from qililab.chip.nodes import Coil, Coupler, Port, Qubit, Resonator
from qililab.constants import RUNCARD
from qililab.settings.ddbb_element import DDBBElement
from qililab.typings import Category
from qililab.typings.enums import Line
from qililab.utils import Factory, dict_factory


@dataclass
class Chip(DDBBElement):
    """Chip representation as a graph."""

    nodes: list[Node]

    def __post_init__(self):
        """Cast nodes and category to their corresponding classes."""
        self.nodes = [Factory.get(name=node.pop(RUNCARD.NAME))(**node) for node in self.nodes]
        self.category = Category(self.category)

    def _get_qubit(self, idx: int) -> Qubit:
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

    def _get_adjacent_nodes(self, node: Node) -> list[Node]:
        """Get adjacent nodes from given node.

        Args:
            node (Node): Node object.

        Returns:
            list[Node]: List containing all adjacent nodes.
        """
        return [self.get_node_from_id(node_id=node_id) for node_id in node.nodes]

    def get_node_from_qubit_idx(self, idx: int, readout: bool) -> Qubit | Resonator:
        """Get node class from qubit index.

        Args:
            idx (int): Qubit index.
            readout (bool): If True, return readout port and resonator frequency, if False return control port and qubit
                frequency.

        Raises:
            ValueError: if qubit doesn't have a readout line

        Returns:
            Qubit | Resonator: qubit/resonator with the given qubit index
        """
        qubit = self._get_qubit(idx=idx)
        if not readout:
            return qubit
        adj_nodes = self._get_adjacent_nodes(node=qubit)
        for node in adj_nodes:
            if isinstance(node, Resonator):
                return node
        raise ValueError(f"Qubit with index {idx} doesn't have a readout line.")

    def get_port_from_qubit_idx(self, idx: int, line: Line) -> int:
        """Find Qubit's port for specific line type

        Args:
            idx (int): Qubit index.
            line (Line): The type of line

        Raises:
            ValueError: If qubit isn't connected to this type of line

        Returns:
            int: The port index
        """
        readout = line in [Line.FEEDLINE_INPUT, Line.FEEDLINE_OUTPUT]
        node = self.get_node_from_qubit_idx(idx=idx, readout=readout)
        adjacent_nodes = self._get_adjacent_nodes(node=node)

        for adjacent_node in adjacent_nodes:
            if isinstance(adjacent_node, Port) and adjacent_node.line == line:
                return adjacent_node.id_

        raise ValueError(f"Qubit with index {idx} doesn't have a {line} line.")

    def get_port_nodes(self, port_id: int) -> list[Qubit | Resonator | Coupler | Coil]:
        """Get nodes connected to a given port.

        Args:
            port (Port): Port class.

        Returns:
            list[Node]: List of nodes connected to the given port.
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
        return None

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
    def qubits(self):
        """Chip `qubits` property.

        Returns:
            list[int]: List of integers containing the indices of the qubits inside the chip.
        """
        return [node.qubit_index for node in self.nodes if isinstance(node, Qubit)]

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
                string += f" * Port {node.id_} ({node.line.value}): ----"
                for adj_node in adj_nodes:
                    string += f"|{adj_node}|--"
                string += "--\n"
        return string
