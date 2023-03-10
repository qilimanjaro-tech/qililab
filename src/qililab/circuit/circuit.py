# pylint: disable=no-member

from dataclasses import asdict, dataclass, field
from tkinter.messagebox import NO
from typing import Tuple

import rustworkx as rx
from rustworkx.visit import BFSVisitor, DFSVisitor, PruneSearch
from rustworkx.visualization import graphviz_draw

from qililab.circuit.nodes import EntryNode, Node, OperationNode
from qililab.circuit.operations import Operation
from qililab.typings.enums import OperationMultiplicity


@dataclass
class Circuit:
    num_qubits: int
    entry_node: EntryNode = field(init=False)
    graph: rx.PyDiGraph = field(init=False)

    def __post_init__(self):
        self.graph = rx.PyDiGraph(multigraph=True)
        self.entry_node = self._add_entry_node()

    def add(self, qubits: int | Tuple[int, ...], operation: Operation, alias: str | None = None):
        qubits = qubits if isinstance(qubits, tuple) else (qubits,)
        if operation._multiplicity == OperationMultiplicity.PARALLEL:
            self._add_parallel_operation(qubits=qubits, operation=operation, alias=alias)
        elif operation._multiplicity == OperationMultiplicity.MULTIPLEXED:
            self._add_multiplexed_operation(qubits=qubits, operation=operation, alias=alias)

    @property
    def depth(self) -> int:
        return len(rx.layers(self.graph, [self.entry_node.index])) - 1

    def _add_parallel_operation(self, qubits: Tuple[int, ...], operation: Operation, alias: str | None = None):
        for qubit in qubits:
            _, last_operation_node = self._last_operation_of_qubit(qubit=qubit)
            new_operation_node = self._add_operation_node(qubits=(qubit,), operation=operation)
            self.graph.add_edge(last_operation_node.index, new_operation_node.index, None)

    def _add_multiplexed_operation(self, qubits: Tuple[int, ...], operation: Operation, alias: str | None = None):
        new_operation_node = self._add_operation_node(qubits=qubits, operation=operation)
        last_operation_nodes = []
        for qubit in qubits:
            _, last_operation_node = self._last_operation_of_qubit(qubit=qubit)
            if last_operation_node not in last_operation_nodes:
                last_operation_nodes.append(last_operation_node)
        if any((isinstance(node, OperationNode) for node in last_operation_nodes)):
            for node in filter(lambda x: isinstance(x, OperationNode), last_operation_nodes):
                self.graph.add_edge(node.index, new_operation_node.index, None)
        else:
            self.graph.add_edge(self.entry_node.index, new_operation_node.index, None)

    def _add_operation_node(
        self, qubits: Tuple[int, ...], operation: Operation, alias: str | None = None
    ) -> OperationNode:
        """Add an operation node to circuit's graph

        Args:
            qubits (Tuple[int]): Tuple of qubits indices
            operation (Operation): The operation
            alias (str | None): Optional alias

        Returns:
            OperationNode: The operation node added
        """
        index = self.graph.add_node(OperationNode(operation=operation, qubits=qubits, alias=alias))
        self.graph[index].index = index
        return self.graph[index]

    def _add_entry_node(self) -> EntryNode:
        """Add the entry point of circuit's graph. Should be called only once on Circuit's `__post_init__()`

        Returns:
            StartNode: The start node added
        """
        index = self.graph.add_node(EntryNode())
        self.graph[index].index = index
        return self.graph[index]

    def _last_operation_of_qubit(self, qubit: int) -> Tuple[int, Node]:
        """Get the last operation node regarding qubit, along with the layer's index the node is

        Args:
            qubit (int): qubit's index

        Returns:
            Tuple[int, Node]: layer, Node
        """
        layer_index, last_operation = 0, self.entry_node
        layers = rx.layers(self.graph, [self.entry_node.index])
        for index, layer in enumerate(layers[1:]):
            for operation in layer:
                if qubit in operation.qubits:
                    layer_index, last_operation = index, operation
        return layer_index, last_operation

    def draw(self, filename: str | None = None):
        def node_attr(node):
            if isinstance(node, EntryNode):
                return {"color": "yellow", "fillcolor": "yellow", "style": "filled", "label": "start"}
            else:
                qubits = ", ".join((str(qubit) for qubit in node.qubits))
                parameters = (
                    "("
                    + ", ".join((f"{parameter}={value}" for parameter, value in node.operation.parameters.items()))
                    + ")"
                    if node.operation.has_parameters()
                    else ""
                )
                label = f"{node.operation.name}{parameters}: {qubits}"
                return {"color": "red", "fillcolor": "red", "style": "filled", "label": label}

        return graphviz_draw(self.graph, node_attr_fn=node_attr, filename=filename)

    def print(self):
        layers = rx.layers(self.graph, [self.entry_node.index])
        for qubit in range(self.num_qubits):
            print(f"{qubit}:", end="")
            for _, layer in enumerate(layers[1:]):
                operations_on_qubit = [operation for operation in layer if qubit in operation.qubits]
                assert len(operations_on_qubit) <= 1
                if len(operations_on_qubit) == 0:
                    print("----------", end="")
                if len(operations_on_qubit) == 1:
                    print(f"{operations_on_qubit[0].operation.name:->10s}", end="")
            print()

    def serialize(self):
        return rx.node_link_json(self.graph)
