
import re
from unittest.mock import MagicMock, call, patch
import pytest
import networkx as nx
from qibo import Circuit, gates
from qibo.transpiler.optimizer import Preprocessing

from qibo.transpiler.placer import ReverseTraversal, StarConnectivityPlacer
from qibo.transpiler.router import Sabre, StarConnectivityRouter
import test

from qililab.digital.circuit_router import CircuitRouter

# Different topologies for testing the routing
linear_connectivity = [(0,1), (1,2), (2,3), (3,4)]
star_connectivity = [(0,1), (0,2), (0,3), (0,4)]

# Linear circuit for testing specific routing
linear_circuit = Circuit(5)
linear_circuit.add(gates.H(0))
linear_circuit.add(gates.CNOT(0, 1))
linear_circuit.add(gates.CNOT(1, 2))
linear_circuit.add(gates.CNOT(2, 3))
linear_circuit.add(gates.CNOT(3, 4))

# Test circuit and layouts for testing the routing
test_circuit = Circuit(5)
test_circuit.add(gates.H(0))

test_circuit_w_swap = Circuit(5)
test_circuit_w_swap.add(gates.SWAP(0,1))


test_layout = {"q1":0}

#########################
### INTEGRATION TESTS ###
#########################
class TestCircuitRouterIntegration:
    """Tests for the circuit router class, integration tests."""

    def test_default_initialization(self):
        """Test the initialization of the CircuitRouter class"""
        connectivity = nx.Graph(linear_connectivity)
        circuit_router = CircuitRouter(connectivity)

        assert circuit_router.connectivity == connectivity
        assert isinstance(circuit_router.preprocessing, Preprocessing)
        assert isinstance(circuit_router.router, Sabre)
        assert isinstance(circuit_router.placer, ReverseTraversal)

    def test_bad_initialization(self):
        """Test the initialization of the CircuitRouter class"""
        connectivity = nx.Graph(linear_connectivity)
        with pytest.raises(ValueError, match="StarConnectivity Placer and Router can only be used with star topologies"):
            circuit_router = CircuitRouter(connectivity, router=StarConnectivityRouter)

    def test_star_initialization(self):
        """Test the initialization of the CircuitRouter class"""
        connectivity = nx.Graph(star_connectivity)
        circuit_router = CircuitRouter(connectivity, router=StarConnectivityRouter, placer=(StarConnectivityPlacer,{"middle_qubit":0} ))

        assert circuit_router.connectivity == connectivity
        assert isinstance(circuit_router.preprocessing, Preprocessing)
        assert isinstance(circuit_router.router, StarConnectivityRouter)
        assert isinstance(circuit_router.placer, StarConnectivityPlacer)
        assert circuit_router.placer.middle_qubit == 0

    def test_route_doesnt_affect_already_routed_circuit(self):
        """Test the routing of a circuit"""
        linear_topology = nx.Graph(linear_connectivity)
        linear_circuit_router = CircuitRouter(linear_topology)

        routed_circuit, final_layout = linear_circuit_router.route(linear_circuit)

        assert final_layout == {"q0":0, "q1":1, "q2":2, "q3":3, "q4":4}
        assert routed_circuit.nqubits == linear_circuit.nqubits
        assert routed_circuit.depth == linear_circuit.depth
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] == [(gate.name, gate.qubits)  for gate in linear_circuit.queue]

    def test_route_affects_non_routed_circuit(self):
        """Test the routing of a circuit"""
        star_topology = nx.Graph(star_connectivity)
        star_circuit_router = CircuitRouter(star_topology)

        routed_circuit, final_layout = star_circuit_router.route(linear_circuit)
        routed_circuit.draw()

        # Assert that the circuit was routed:
        assert final_layout != {"q0":0, "q1":1, "q2":2, "q3":3, "q4":4}
        assert routed_circuit.nqubits == linear_circuit.nqubits
        assert routed_circuit.depth > linear_circuit.depth
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] != [(gate.name, gate.qubits)  for gate in linear_circuit.queue]
        assert {gate.name for gate in routed_circuit.queue} >= {gate.name for gate in linear_circuit.queue} # Assert more gates

        # Assert that the circuit is routed in a concrete way:
        assert final_layout == {'q0': 3, 'q1': 1, 'q2': 2, 'q3': 0, 'q4': 4}
        assert routed_circuit.draw() == 'q0: ───X─o─x─X─o─\nq1: ───|─|─x─|─|─\nq2: ───|─X───o─|─\nq3: ─H─o───────|─\nq4: ───────────X─'


##################
### UNIT TESTS ###
##################
class TestCircuitRouterUnit:
    """Tests for the circuit router class, unit tests."""

    topology = nx.Graph(star_connectivity)
    circuit_router = CircuitRouter(topology)

    @patch("qililab.config.logger.info")
    @patch("qililab.digital.circuit_router.CircuitRouter._iterate_routing", return_value=(test_circuit, test_layout, 0))
    def test_route(self, mock_iterate, mock_logger_info):
        """ Test the routing of a circuit."""
        routed_circuit, final_layout = self.circuit_router.route(linear_circuit)

        # Assert that the routing pipeline was called with the correct arguments
        mock_iterate.assert_called_once_with(self.circuit_router.pipeline, linear_circuit, 10)

        # Assert that the logger is called
        mock_logger_info.assert_called_once_with("The best found routing, has 0 swaps.")

        # Assert you return the same outputs as the mocked _iterate_routing
        assert (routed_circuit, final_layout) == (test_circuit, test_layout)

    @patch("qililab.digital.circuit_router.Passes.__call__", return_value=(test_circuit, test_layout))
    def test_iterate_routing_without_swaps(self, mock_qibo_routing):
        """ Test the iterate routing of a circuit, without swaps."""
        routed_circuit, final_layout, least_swaps = self.circuit_router._iterate_routing(self.circuit_router.pipeline, linear_circuit)

        # Assert only called once, since there are no swaps:
        mock_qibo_routing.assert_called_once_with(linear_circuit)

        # Assert you return the correct outputs:
        assert (routed_circuit, final_layout, least_swaps) == (test_circuit, test_layout, 0)

    @patch("qililab.digital.circuit_router.Passes.__call__", return_value=(test_circuit_w_swap, test_layout))
    def test_iterate_routing_with_swaps(self, mock_qibo_routing):
        """ Test the iterate routing of a circuit, with swaps."""
        iterations = 7

        routed_circuit, final_layout, least_swaps = self.circuit_router._iterate_routing(self.circuit_router.pipeline, linear_circuit, iterations)

        # Assert called as many times as number of iterations, since there are swaps present:
        mock_qibo_routing.assert_has_calls([call(linear_circuit)]*iterations)

         # Assert you return the correct outputs:
        assert (routed_circuit, final_layout, least_swaps) == (test_circuit_w_swap, test_layout, 1)
