import re
from unittest.mock import call, patch
import pytest
import networkx as nx
from qibo import Circuit, gates
from qibo.transpiler.optimizer import Preprocessing

from qibo.transpiler.placer import ReverseTraversal, StarConnectivityPlacer, Trivial
from qibo.transpiler.router import Sabre, StarConnectivityRouter

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

    linear_topology = nx.Graph(linear_connectivity)
    star_topology = nx.Graph(star_connectivity)

    linear_circuit_router = CircuitRouter(linear_topology)
    star_circuit_router = CircuitRouter(star_topology)

    def test_default_initialization(self):
        """Test the initialization of the CircuitRouter class"""
        assert self.linear_circuit_router.connectivity == self.linear_topology
        assert isinstance(self.linear_circuit_router.preprocessing, Preprocessing)
        assert isinstance(self.linear_circuit_router.router, Sabre)
        assert isinstance(self.linear_circuit_router.placer, ReverseTraversal)

    def test_bad_initialization(self):
        """Test the initialization of the CircuitRouter class"""
        with pytest.raises(ValueError, match="StarConnectivity Placer and Router can only be used with star topologies"):
            circuit_router = CircuitRouter(self.linear_topology, router=StarConnectivityRouter)

    def test_star_initialization(self):
        """Test the initialization of the CircuitRouter class"""

        circuit_router = CircuitRouter(self.star_topology, router=StarConnectivityRouter, placer=(StarConnectivityPlacer,{"middle_qubit":0} ))

        assert circuit_router.connectivity == self.star_topology
        assert isinstance(circuit_router.preprocessing, Preprocessing)
        assert isinstance(circuit_router.router, StarConnectivityRouter)
        assert isinstance(circuit_router.placer, StarConnectivityPlacer)
        assert circuit_router.placer.middle_qubit == 0

    def test_route_doesnt_affect_already_routed_circuit(self):
        """Test the routing of a circuit"""
        routed_circuit, final_layout = self.linear_circuit_router.route(linear_circuit)

        assert final_layout == {"q0":0, "q1":1, "q2":2, "q3":3, "q4":4}
        assert routed_circuit.nqubits == linear_circuit.nqubits
        assert routed_circuit.depth == linear_circuit.depth
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] == [(gate.name, gate.qubits)  for gate in linear_circuit.queue]

    def test_route_affects_non_routed_circuit(self):
        """Test the routing of a circuit"""

        routed_circuit, final_layout = self.star_circuit_router.route(linear_circuit)
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

    linear_topology = nx.Graph(linear_connectivity)
    star_topology = nx.Graph(star_connectivity)

    circuit_router = CircuitRouter(linear_topology)

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

    def test_if_star_algorithms_for_nonstar_connectivity(self):
        """Test the routing of a circuit"""
        circ_router = self.circuit_router

        # Assert cases where it needs to return True
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(self.linear_topology, StarConnectivityPlacer(), circ_router.router)
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(self.linear_topology, Trivial(), StarConnectivityRouter())
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(self.linear_topology, StarConnectivityPlacer(), StarConnectivityRouter())

        # Assert cases where it needs to return False
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(self.linear_topology, Trivial(), circ_router.router)
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(self.star_topology, Trivial(), StarConnectivityRouter())
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(self.star_topology, circ_router.placer, circ_router.router)

    def test_highest_degree_node(self):
        """Test the _highest_degree_node method."""
        # Test new edited linear topology
        edited_linear_topology = nx.Graph(linear_connectivity)
        edited_linear_topology.add_edges_from([(2,3),(2,4)])
        assert self.circuit_router._highest_degree_node(edited_linear_topology) == 2

        # Test the star topology with the 0 as central
        assert self.circuit_router._highest_degree_node(self.star_topology) == 0

    @patch("qililab.digital.circuit_router.CircuitRouter._check_ReverseTraversal_routing_connectivity")
    def test_build_placer(self, mock_check_reverse):
        """Test the _build_placer method."""

        # Test default placer (ReverseTraversal)
        placer = self.circuit_router._build_placer(None, self.circuit_router.router, self.linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (self.linear_topology, self.circuit_router.router)

        # Test Trivial placer
        placer = self.circuit_router._build_placer(Trivial, self.circuit_router.router, self.linear_topology)
        assert isinstance(placer, Trivial)
        assert placer.connectivity == self.linear_topology
        assert hasattr(placer, "routing_algorithm") == False

        # Test StarConnectivityPlacer with kwargs
        placer = self.circuit_router._build_placer((StarConnectivityPlacer, {"middle_qubit": 0}), self.circuit_router.router, self.star_topology)
        assert isinstance(placer, StarConnectivityPlacer)
        assert placer.middle_qubit == 0
        assert hasattr(placer, "routing_algorithm") == hasattr(placer, "connectivity") == False

        # Test ReverseTraversal with kwargs
        mock_check_reverse.return_value = (ReverseTraversal, {"routing_algorithm": self.circuit_router.router})
        placer = self.circuit_router._build_placer((ReverseTraversal, {"routing_algorithm": self.circuit_router.router}), self.circuit_router.router, self.linear_topology)
        mock_check_reverse.assert_called_once_with(ReverseTraversal, {"routing_algorithm": self.circuit_router.router}, self.linear_topology, self.circuit_router.router)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (self.linear_topology, self.circuit_router.router)

        # Test invalid placer type
        with pytest.raises(TypeError, match="`placer` arg"):
            self.circuit_router._build_placer("invalid_placer", self.circuit_router.router, self.linear_topology)

        # Test Placer instance, instead than subclass:
        trivial_placer_instance = Trivial(self.linear_topology)
        placer = self.circuit_router._build_placer(trivial_placer_instance, self.circuit_router.router, self.linear_topology)
        assert isinstance(placer, Trivial)
        assert placer.connectivity == self.linear_topology
        assert hasattr(placer, "routing_algorithm") == False

        star_placer_instance = StarConnectivityPlacer(self.star_topology, middle_qubit=2)
        placer = self.circuit_router._build_placer(star_placer_instance, self.circuit_router.router, self.star_topology)
        assert isinstance(placer, StarConnectivityPlacer)
        assert placer.middle_qubit == 0
        assert hasattr(placer, "routing_algorithm") == hasattr(placer, "connectivity") == False

        reverse_traversal_instance = ReverseTraversal(self.linear_topology, self.circuit_router.router)
        placer = self.circuit_router._build_placer(reverse_traversal_instance, self.circuit_router.router, self.linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (self.linear_topology, self.circuit_router.router)

    def test_build_router(self):
        """Test the _build_router method."""

        # Test default router (Sabre)
        router = self.circuit_router._build_router(None, self.linear_topology)
        assert isinstance(router, Sabre)
        assert router.connectivity == self.linear_topology

        # Test StarConnectivityRouter
        router = self.circuit_router._build_router(StarConnectivityRouter, self.star_topology)
        assert isinstance(router, StarConnectivityRouter)
        assert router.middle_qubit == 0
        assert  hasattr(router, "connectivity") == False

        # Test Sabre router with kwargs
        router = self.circuit_router._build_router((Sabre, {"lookahead": 2}), self.linear_topology)
        assert isinstance(router, Sabre)
        assert router.connectivity == self.linear_topology
        assert router.lookahead == 2

        # Test invalid router type
        with pytest.raises(TypeError, match="`router` arg"):
            self.circuit_router._build_router("invalid_router", self.linear_topology)

        # Test Router instance, instead of subclass
        sabre_instance = Sabre(self.linear_topology)
        router = self.circuit_router._build_router(sabre_instance, self.linear_topology)
        assert isinstance(router, Sabre)
        assert router.connectivity == self.linear_topology

        star_router_instance = StarConnectivityRouter(self.star_topology)
        router = self.circuit_router._build_router(star_router_instance, self.star_topology)
        assert isinstance(router, StarConnectivityRouter)
        assert router.middle_qubit == 0
        assert  hasattr(router, "connectivity") == False

    def test_check_reverse_traversal_routing_connectivity(self):
        """Test the _check_ReverseTraversal_routing_connectivity method."""
        # Test for a linear topology
        og_placer = ReverseTraversal
        og_kwargs = {"routing_algorithm": Sabre}
        router = Sabre

        # Check with placer and routing algorithm both subclasses
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, self.linear_topology, router)
        assert (placer, kwargs) == (og_placer, og_kwargs)

        # Test for a weird router of the reversal
        og_kwargs = {"routing_algorithm": int, "lookahead": 2}
        with pytest.raises(TypeError, match=re.escape("`routing_algorithm` `Placer` kwarg (<class 'int'>) must be a `Router` subclass or instance, in `execute()`, `compile()`, `transpile_circuit()` or `route_circuit()`.")):
            self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, self.star_topology, router)

        # Test that the routing_algorithm get automatically inserted:
        og_kwargs = {"lookahead": 2}
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, self.linear_topology, router)
        assert (placer, kwargs) == (og_placer, og_kwargs | {"routing_algorithm": router})

        # Test instance of Router, change to chips topology:
        og_kwargs = {"routing_algorithm": Sabre(connectivity=None)}
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, self.linear_topology, router)
        og_kwargs["routing_algorithm"].connectivity = self.linear_topology
        assert (placer, kwargs) == (og_placer, og_kwargs)

        # Test subclass of Router, change to chips topology:
        og_kwargs = {"routing_algorithm": Sabre(connectivity=None)}
        og_placer = ReverseTraversal(connectivity=self.linear_topology, routing_algorithm=og_kwargs["routing_algorithm"])
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, self.linear_topology, router)
        assert og_placer.routing_algorithm.connectivity == self.linear_topology
        assert (placer, kwargs) == (og_placer, og_kwargs)
