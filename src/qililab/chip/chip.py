# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Chip class."""
from dataclasses import asdict, dataclass

import networkx as nx
from networkx import Graph

from qililab.chip.node import Node
from qililab.chip.nodes import Coil, Coupler, Port, Qubit, Resonator
from qililab.constants import RUNCARD
from qililab.typings.enums import Line
from qililab.utils import Factory, dict_factory


@dataclass
class Chip:
    """Chip representation as a graph.
    This class represents the chip structure of in the runcard and contains all the connectivity information of
    the chip.
    """

    nodes: list[Node]

    def __post_init__(self):
        """Cast nodes to their corresponding classes."""
        self.nodes = [Factory.get(name=node.pop(RUNCARD.NAME))(**node) for node in self.nodes]

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

    def _get_adjacent_nodes(self, node: Node) -> list[Node | None]:
        """Get adjacent nodes from given node.

        Args:
            node (Node): Node object.

        Returns:
            list[Node | None]: List containing all adjacent nodes.
        """
        return [self.get_node_from_alias(alias=alias) for alias in node.nodes]

    def get_topology(self) -> Graph:
        """Returns a networkx Graph with the qubit connectivity of the chip

        Returns:
            Graph: graph showing the qubit topology
        """
        g = nx.Graph()

        for qubit in self.qubits:
            neighs = [
                neigh
                for neigh in self._get_adjacent_nodes(self.get_node_from_qubit_idx(qubit, readout=False))
                if isinstance(neigh, Qubit)
            ]
            neigh_qubits = [neigh.qubit_index for neigh in neighs if isinstance(neigh, Qubit)]
            edges = [(qubit, neigh_qubit) for neigh_qubit in neigh_qubits]
            g.add_edges_from(edges)
        return g

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

    def get_port_from_qubit_idx(self, idx: int, line: Line) -> str:
        """Find Qubit's port for specific line type

        Args:
            idx (int): Qubit index.
            line (Line): The type of line

        Raises:
            ValueError: If qubit isn't connected to this type of line

        Returns:
            str: The alias of the port
        """
        readout = line in [Line.FEEDLINE_INPUT, Line.FEEDLINE_OUTPUT]
        node = self.get_node_from_qubit_idx(idx=idx, readout=readout)
        adjacent_nodes = self._get_adjacent_nodes(node=node)

        for adjacent_node in adjacent_nodes:
            if isinstance(adjacent_node, Port) and adjacent_node.line == line:
                return adjacent_node.alias

        raise ValueError(f"Qubit with index {idx} doesn't have a {line} line.")

    def get_port_nodes(self, alias: str) -> list[Qubit | Resonator | Coupler | Coil]:
        """Get nodes connected to a given port.

        Args:
            alias (str): Alias of the port.

        Returns:
            list[Node]: List of nodes connected to the given port.
        """
        port = self.get_node_from_alias(alias=alias)
        return self._get_adjacent_nodes(node=port)  # type: ignore

    def get_node_from_alias(self, alias: str) -> Node | None:
        """Get node from given alias.

        Args:
            alias (str): Alias of the node.

        Raises:
            ValueError: If no node is found.

        Returns:
            Node | None: Node class.
        """
        for node in self.nodes:
            if node.alias == alias:
                return node
        return None

    def to_dict(self):
        """Return a dict representation of the Chip class."""
        return {
            "nodes": [{RUNCARD.NAME: node.name.value} | asdict(node, dict_factory=dict_factory) for node in self.nodes]
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
        string = f"Chip with {self.num_qubits} qubits and {self.num_ports} ports: \n\n"
        for node in self.nodes:
            if isinstance(node, Port):
                adj_nodes = self._get_adjacent_nodes(node=node)
                string += f" * Port {node.alias} ({node.line.value}): ----"
                for adj_node in adj_nodes:
                    string += f"|{adj_node}|--"
                string += "--\n"
        return string
