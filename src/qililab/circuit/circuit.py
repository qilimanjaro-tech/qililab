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

"""Circuit class

This file provides the Circuit class for representing quantum circuits.

It stores the circuit as a Directed Acyclic Graph and uses the rustworkx library for its manipulation.
It offers methods to add operations to the circuit, calculate the circuit's depth, and visualize the circuit.
"""
import rustworkx as rx
from rustworkx.visualization import graphviz_draw

from qililab.circuit.nodes import EntryNode, Node, OperationNode
from qililab.circuit.operations import Operation
from qililab.typings.enums import OperationTimingsCalculationMethod, Qubits


class Circuit:
    """The Circuit class"""

    def __init__(self, num_qubits: int):
        """Constructor of Circuit

        Args:
            num_qubits (int): The number of qubits of the circuit

        Raises:
            ValueError: If num_qubits is not integer.
            ValueError: If num_qubits is not positive.
        """
        if not isinstance(num_qubits, int):
            raise ValueError("Number of qubits should be integer.")
        if num_qubits <= 0:
            raise ValueError("Number of qubits should be positive.")

        self.num_qubits: int = num_qubits
        self.graph: rx.PyDiGraph = rx.PyDiGraph(multigraph=True)  # pylint: disable=no-member
        self.has_timings_calculated: bool = False
        self.has_special_operations_removed: bool = False
        self.has_transpiled_to_pulses: bool = False

        index = self.graph.add_node(EntryNode())
        self.graph[index].index = index
        self.entry_node = self.graph[index]

    def add(self, qubits: int | tuple[int, ...], operation: Operation, alias: str | None = None):
        """Adds an operation to the circuit.

        Args:
            qubits (int | tuple[int, ...]): The qubit(s) the operation acts on
            operation (Operation): The operation to add
            alias (str | None, optional): Optional alias for the operation. Defaults to None.
        """
        self._reset_transpilation_flags()
        qubits = qubits if isinstance(qubits, tuple) else (qubits,)
        if (operation.num_qubits == Qubits.ONE and len(qubits) != 1) or (
            operation.num_qubits == Qubits.TWO and len(qubits) != 2
        ):
            raise ValueError("Number of qubits does not match operation's num_qubits attribute")
        self._add_operation(qubits=qubits, operation=operation, alias=alias)

    def _add_operation(self, qubits: tuple[int, ...], operation: Operation, alias: str | None = None):
        """Adds one operation node for all qubits

        Args:
            qubits (tuple[int, ...]): The qubits the operation acts on
            operation (Operation): The operation to add
            alias (str | None, optional): Optional alias for the operation. Defaults to None.
        """
        new_operation_node = self._add_operation_node(qubits=qubits, operation=operation, alias=alias)
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
        self, qubits: tuple[int, ...], operation: Operation, alias: str | None = None
    ) -> OperationNode:
        """Add an operation node to circuit's graph

        Args:
            qubits (tuple[int]): Tuple of qubits indices
            operation (Operation): The operation
            alias (str | None): Optional alias

        Returns:
            OperationNode: The operation node added
        """
        index = self.graph.add_node(OperationNode(operation=operation, qubits=qubits, alias=alias))
        self.graph[index].index = index
        return self.graph[index]

    def _last_operation_of_qubit(self, qubit: int) -> tuple[int, Node]:
        """Get the last operation node regarding qubit, along with the layer's index. If no operation found returns the entry node.

        Args:
            qubit (int): qubit's index

        Returns:
            tuple[int, Node]: layer index, Node
        """
        layers = rx.layers(self.graph, [self.entry_node.index])  # pylint: disable=no-member
        for index, layer in reversed(list(enumerate(layers[1:]))):
            for operation in layer:
                if qubit in operation.qubits:
                    return index, operation
        return 0, self.entry_node

    def _reset_transpilation_flags(self) -> None:
        """Reset the flags used for transpilation process"""
        self.has_timings_calculated = False
        self.has_special_operations_removed = False
        self.has_transpiled_to_pulses = False

    @property
    def depth(self) -> int:
        """Get the depth of the circuit which is essentially the number of operation layers

        Returns:
            int: The depth of the circuit
        """
        return len(rx.layers(self.graph, [self.entry_node.index])) - 1  # pylint: disable=no-member

    def get_operation_layers(
        self, method: OperationTimingsCalculationMethod = OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE
    ) -> list[list[OperationNode]]:
        """Get the layers of operation nodes. Each layer represents an advancement in time.

        Args:
            method (OperationTimingsCalculationMethod, optional): The method that layers should be calculated.
                If set to `OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE`, we rearrange the layers, moving
                operations to the largest layer index possible. Defaults to
                OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE.

        Returns:
            list[list[OperationNode]]: A list of layers each containing a list of operation nodes.
                Operation nodes are sorted based on their index. (order of insertion)
        """
        layers = rx.layers(self.graph, [self.entry_node.index])[1:]  # pylint: disable=no-member
        for layer in layers:
            layer.sort(key=lambda node: node.index)
        if method == OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE:
            return layers
        for qubit in range(self.num_qubits):
            for index, layer in enumerate(layers):
                current_single_operations_on_qubit = [
                    op_i
                    for op_i, operation in enumerate(layer)
                    if qubit in operation.qubits and len(operation.qubits) == 1
                ]
                if len(current_single_operations_on_qubit) == 0:
                    continue
                if index == len(layers) - 1:
                    continue
                next_layer_operations_on_qubit = [
                    operation for operation in layers[index + 1] if qubit in operation.qubits
                ]
                if len(next_layer_operations_on_qubit) == 0:
                    layers[index + 1].append(layer.pop(current_single_operations_on_qubit[0]))
        return layers

    def draw(self, filename: str | None = None):
        """Draws the circuit's graph.

        Args:
            filename (str | None, optional): If set, the result is saved to a file. Defaults to None.
        """

        def node_attr(node):
            if isinstance(node, EntryNode):
                return {"color": "yellow", "fillcolor": "yellow", "style": "filled", "label": "start"}
            operation = str(node.operation)
            qubits = ", ".join((str(qubit) for qubit in node.qubits))
            timing = f"{node.timing.start}ns -> {node.timing.end}ns" if node.timing is not None else ""
            label = f"{operation}: {qubits}\n{timing}"
            return {"color": "red", "fillcolor": "red", "style": "filled", "label": label}

        image = graphviz_draw(self.graph, node_attr_fn=node_attr, filename=filename)
        if image is not None:
            image.show()

    def print(self, method: OperationTimingsCalculationMethod = OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE):
        """Prints the circuit to the standard output.

        Args:
            method (OperationTimingsCalculationMethod, optional): Defaults to OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE.
        """
        layers = self.get_operation_layers(method=method)
        for qubit in range(self.num_qubits):
            print(f"{qubit}:", end="")
            for _, layer in enumerate(layers):
                operations_on_qubit = [operation for operation in layer if qubit in operation.qubits]
                if len(operations_on_qubit) == 0:
                    print("----------", end="")
                if len(operations_on_qubit) == 1:
                    print(f"{operations_on_qubit[0].operation.name.value:->10s}", end="")
            print()
