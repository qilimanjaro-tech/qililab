# pylint: disable=no-member

"""Tests for the Operation class."""
from typing import Tuple

import pytest
import rustworkx as rx

from qililab.circuit import Circuit
from qililab.circuit.nodes import EntryNode, Node, OperationNode
from qililab.circuit.operations import (
    R180,
    Barrier,
    Measure,
    Operation,
    Reset,
    Rxy,
    Wait,
    X,
)
from qililab.typings.enums import OperationMultiplicity


@pytest.fixture(name="simple_circuit")
def fixture_simple_circuit() -> Circuit:
    """Return a simple circuit."""
    circuit = Circuit(2)
    circuit.add(0, X())
    circuit.add(0, Wait(t=100))
    circuit.add(0, X())
    circuit.add(1, X())
    circuit.add((0, 1), Measure())
    return circuit


@pytest.fixture(name="empty_circuit")
def fixture_empty_circuit() -> Circuit:
    """Return a simple circuit."""
    circuit = Circuit(2)
    return circuit


class TestCircuit:
    """Unit tests checking the Circuit attributes and methods"""

    @pytest.mark.parametrize("num_qubits", [1, 10, 1000])
    def test_num_qubits_property(self, num_qubits: int):
        """Test num_qubits property"""
        circuit = Circuit(num_qubits=num_qubits)
        assert isinstance(circuit.num_qubits, int)
        assert circuit.num_qubits == num_qubits

    @pytest.mark.parametrize("num_qubits", [-10, -1, 0])
    def test_constructor_raises_error_when_num_qubits_is_not_positive(self, num_qubits: int):
        with pytest.raises(ValueError, match="Number of qubits should be positive."):
            Circuit(num_qubits=num_qubits)

    @pytest.mark.parametrize("num_qubits", [1.0, 5.2, 10e9])
    def test_constructor_raises_error_when_num_qubits_is_not_integer(self, num_qubits: int):
        with pytest.raises(ValueError, match="Number of qubits should be integer."):
            Circuit(num_qubits=num_qubits)

    def test_graph_is_valid(self, simple_circuit: Circuit):
        assert isinstance(simple_circuit.graph, rx.PyDiGraph)
        assert simple_circuit.graph.multigraph is True
        assert isinstance(simple_circuit.entry_node, EntryNode)
        assert isinstance(simple_circuit.entry_node.index, int)

    def test_depth_parameter(self, simple_circuit: Circuit):
        depth = simple_circuit.depth
        assert isinstance(depth, int)
        assert depth == 4

    @pytest.mark.parametrize("qubits,operation", [(0, X()), (1, X()), (0, Reset()), ((0, 1), Reset())])
    def test_add_method_that_should_add_one_node(
        self, simple_circuit: Circuit, qubits: int | Tuple[int, ...], operation: Operation
    ):
        number_of_nodes_before = simple_circuit.graph.num_nodes()
        num_qubits = len(qubits) if isinstance(qubits, tuple) else 1
        number_of_nodes_that_should_be_added = (
            num_qubits if operation.multiplicity == OperationMultiplicity.PARALLEL else 1
        )
        simple_circuit.add(qubits=qubits, operation=operation)
        number_of_nodes_after = simple_circuit.graph.num_nodes()
        assert number_of_nodes_after == number_of_nodes_before + number_of_nodes_that_should_be_added
