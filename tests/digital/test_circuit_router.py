import re
from unittest.mock import call, patch
import pytest
import networkx as nx
from qibo import Circuit, gates
from qibo.transpiler.optimizer import Preprocessing

from qibo.transpiler.placer import ReverseTraversal, StarConnectivityPlacer, Trivial
from qibo.transpiler.router import Sabre, StarConnectivityRouter

from qililab.digital.circuit_router import CircuitRouter

# Different connectivities for testing the routing
linear_connectivity = [(0,1), (1,2), (2,3), (3,4)]
star_connectivity = [(0,1), (0,2), (0,3), (0,4)]

# Different topologies for testing the routing
linear_topology = nx.Graph(linear_connectivity)
star_topology = nx.Graph(star_connectivity)

# Linear circuit for testing specific routing
linear_circuit = Circuit(5)
linear_circuit.add(gates.H(0))
linear_circuit.add(gates.CNOT(0, 1))
linear_circuit.add(gates.CNOT(1, 2))
linear_circuit.add(gates.CNOT(2, 3))
linear_circuit.add(gates.CNOT(3, 4))

# Tests circuit
test_circuit = Circuit(5)
test_circuit.add(gates.H(0))
# Tests circuit with SWAP
test_circuit_w_swap = Circuit(5)
test_circuit_w_swap.add(gates.SWAP(0,1))
# Tests layouts
test_layout = {"q1":0}
test_bad_layout = {"q0":0, "q1":0}

#########################
### INTEGRATION TESTS ###
#########################
class TestCircuitRouterIntegration:
    """Tests for the circuit router class, integration tests."""

    @pytest.mark.parametrize(
        "type, topology",
        [("linear", linear_topology), ("star", star_topology), ("bad", linear_topology)]
    )
    def test_initialization(self, type, topology):
        """Test the initialization of the CircuitRouter class"""
        # Test the incorrect initialization of the CircuitRouter class
        if type == "bad":
            with pytest.raises(ValueError, match="StarConnectivity Placer and Router can only be used with star topologies"):
                _ = CircuitRouter(topology, router=StarConnectivityRouter)

        # Test the correct initialization of the CircuitRouter class
        elif type == "linear":
            router = CircuitRouter(topology, router=Sabre, placer=ReverseTraversal)
            assert isinstance(router.placer, ReverseTraversal)
            assert isinstance(router.router, Sabre)
        elif type == "star":
            router = CircuitRouter(topology, router=StarConnectivityRouter, placer=StarConnectivityPlacer)
            assert isinstance(router.placer, StarConnectivityPlacer)
            assert isinstance(router.router, StarConnectivityRouter)
            assert router.placer.middle_qubit == 0
        if type in ["linear", "star"]:
            assert router.connectivity == topology
            assert isinstance(router.preprocessing, Preprocessing)

    def test_route_doesnt_affect_already_routed_circuit(self):
        """Test the routing of a circuit"""
        routed_circuit, final_layout = CircuitRouter(linear_topology).route(linear_circuit)

        assert final_layout == {"q0":0, "q1":1, "q2":2, "q3":3, "q4":4}
        assert routed_circuit.nqubits == linear_circuit.nqubits
        assert routed_circuit.depth == linear_circuit.depth
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] == [(gate.name, gate.qubits)  for gate in linear_circuit.queue]

    def test_route_affects_non_routed_circuit(self):
        """Test the routing of a circuit"""

        routed_circuit, final_layout = CircuitRouter(star_topology).route(linear_circuit)

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

    circuit_router = CircuitRouter(linear_topology)

    @pytest.mark.parametrize(
        "type, circuit, layout, least_swaps",
        [
            ("good", test_circuit, test_layout, 0),
            ("none_swaos", test_circuit, test_layout, None),
            ("bad_layout", test_circuit, test_bad_layout, 0)
        ]
    )
    @patch("qililab.config.logger.info")
    @patch("qililab.digital.circuit_router.CircuitRouter._iterate_routing")
    def test_route(self, mock_iterate, mock_logger_info, type, circuit, layout, least_swaps):
        """Test the routing of a circuit."""
        # Set the mock returns to the parametrized test values:
        mock_iterate.return_value = (circuit, layout, least_swaps)

        # Execute the routing:
        if type in ["good", "none_swaos"]:
            routed_circuit, final_layout = self.circuit_router.route(linear_circuit)
            # Assert you return the same outputs as the mocked _iterate_routing
            assert (routed_circuit, final_layout) ==(test_circuit, test_layout)
        elif type == "bad_layout":
            with pytest.raises(ValueError, match=re.escape(f"The final layout: {test_bad_layout} is not valid. i.e. a qubit is mapped to more than one physical qubit. Try again, if the problem persists, try another placer/routing algorithm.")):
                _, _ = self.circuit_router.route(linear_circuit)

        # Assert that the logger is called properly
        if type == "good":
            mock_logger_info.assert_called_once_with("The best found routing, has 0 swaps.")
        elif type == "none_swaos":
            mock_logger_info.assert_called_once_with("No routing was done. Most probably due to routing iterations being 0.")
        elif type == "bad_layout":
            mock_logger_info.assert_not_called()

        # Assert that the routing pipeline was called with the correct arguments
        mock_iterate.assert_called_once_with(self.circuit_router.pipeline, linear_circuit, 10)

    @pytest.mark.parametrize(
        "type, circuit, layout, least_swaps, iterations",
        [
            ("without_swaps", test_circuit, test_layout, None, 10),
            ("with_swaps", test_circuit_w_swap, test_layout, 1, 7),

        ]
    )
    @patch("qililab.digital.circuit_router.Passes.__call__")
    def test_iterate_routing_without_swaps(self, mock_qibo_routing, type, circuit, layout, least_swaps, iterations):
        """ Test the iterate routing of a circuit, with and without swaps."""
        # Add the mock return value to the parametrized test values:
        mock_qibo_routing.return_value = (circuit, layout)

        # Execute the iterate_routing:
        routed_circuit, final_layout, least_swaps = self.circuit_router._iterate_routing(self.circuit_router.pipeline, linear_circuit, iterations)

        # Assert calls on the routing algorithm:
        if type == "with_swaps":
            # Assert called as many times as number of iterations, since there are swaps present:
            mock_qibo_routing.assert_has_calls([call(linear_circuit)]*iterations)
            expected_least_swaps = 1
        elif type == "without_swaps":
            # Assert only called once, since there are no swaps:
            mock_qibo_routing.assert_called_once_with(linear_circuit)
            expected_least_swaps = iterations = 0 # Since there are no swaps, no iterations have been needed

        # Assert you return the correct outputs:
        assert (routed_circuit, final_layout, least_swaps) == (circuit, layout, expected_least_swaps)

    def test_if_star_algorithms_for_nonstar_connectivity(self):
        """Test the routing of a circuit"""
        circ_router = self.circuit_router

        # Assert cases where it needs to return True
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, StarConnectivityPlacer(), circ_router.router)
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, Trivial(), StarConnectivityRouter())
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, StarConnectivityPlacer(), StarConnectivityRouter())

        # Assert cases where it needs to return False
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, Trivial(), circ_router.router)
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(star_topology, Trivial(), StarConnectivityRouter())
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(star_topology, circ_router.placer, circ_router.router)

    def test_highest_degree_node(self):
        """Test the _highest_degree_node method."""
        # Test new edited linear topology
        edited_linear_topology = nx.Graph(linear_connectivity)
        edited_linear_topology.add_edges_from([(2,3),(2,4)])
        assert self.circuit_router._highest_degree_node(edited_linear_topology) == 2

        # Test the star topology with the 0 as central
        assert self.circuit_router._highest_degree_node(star_topology) == 0

    def test_if_layout_is_not_valid(self):
        """Test the _if_layout_is_not_valid method."""
        # Test valid layout
        assert not self.circuit_router._if_layout_is_not_valid(test_layout)

        # Test invalid layout
        assert self.circuit_router._if_layout_is_not_valid(test_bad_layout)

    @patch("qililab.digital.circuit_router.CircuitRouter._check_ReverseTraversal_routing_connectivity")
    @patch("qililab.digital.circuit_router.logger.warning")
    def test_build_placer(self, mock_logger_warning, mock_check_reverse):
        """Test the _build_placer method."""

        # Test default placer (ReverseTraversal)
        placer = self.circuit_router._build_placer(None, self.circuit_router.router, linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (linear_topology, self.circuit_router.router)

        # Test Trivial placer
        placer = self.circuit_router._build_placer(Trivial, self.circuit_router.router, linear_topology)
        assert isinstance(placer, Trivial)
        assert placer.connectivity == linear_topology
        assert hasattr(placer, "routing_algorithm") == False

        # Test StarConnectivityPlacer with kwargs
        placer = self.circuit_router._build_placer((StarConnectivityPlacer, {"middle_qubit": 0}), self.circuit_router.router, star_topology)
        assert isinstance(placer, StarConnectivityPlacer)
        assert placer.middle_qubit == 0
        assert hasattr(placer, "routing_algorithm") == hasattr(placer, "connectivity") == False

        # Test ReverseTraversal with kwargs
        mock_check_reverse.return_value = (ReverseTraversal, {"routing_algorithm": self.circuit_router.router})
        placer = self.circuit_router._build_placer((ReverseTraversal, {"routing_algorithm": self.circuit_router.router}), self.circuit_router.router, linear_topology)
        mock_check_reverse.assert_called_once_with(ReverseTraversal, {"routing_algorithm": self.circuit_router.router}, linear_topology, self.circuit_router.router)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (linear_topology, self.circuit_router.router)

        # Test invalid placer type
        with pytest.raises(TypeError, match="`placer` arg"):
            self.circuit_router._build_placer("invalid_placer", self.circuit_router.router, linear_topology)

        # Test Placer instance, instead than subclass:
        trivial_placer_instance = Trivial(linear_topology)
        mock_logger_warning.reset_mock()
        placer = self.circuit_router._build_placer(trivial_placer_instance, self.circuit_router.router, linear_topology)
        assert isinstance(placer, Trivial)
        assert placer.connectivity == linear_topology
        assert hasattr(placer, "routing_algorithm") == False
        mock_logger_warning.assert_has_calls([call("Substituting the placer connectivity by the transpiler/platform one.")])

        star_placer_instance = StarConnectivityPlacer(star_topology, middle_qubit=2)
        mock_logger_warning.reset_mock()
        placer = self.circuit_router._build_placer(star_placer_instance, self.circuit_router.router, star_topology)
        assert isinstance(placer, StarConnectivityPlacer)
        assert placer.middle_qubit == 0
        assert hasattr(placer, "routing_algorithm") == hasattr(placer, "connectivity") == False
        mock_logger_warning.assert_has_calls([call("Substituting the placer connectivity by the transpiler/platform one.")])

        reverse_traversal_instance = ReverseTraversal(linear_topology, self.circuit_router.router)
        placer = self.circuit_router._build_placer(reverse_traversal_instance, self.circuit_router.router, linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (linear_topology, self.circuit_router.router)

        # Test Router instance, with kwargs:
        placer_instance = Trivial()
        placer_kwargs = {"lookahead": 3}
        mock_logger_warning.reset_mock()
        router = self.circuit_router._build_placer((placer_instance,placer_kwargs),self.circuit_router.router, linear_topology)
        assert hasattr(router, "lookahead") == False
        mock_logger_warning.assert_has_calls([call("Ignoring placer kwargs, as the placer is already an instance."),
            call("Substituting the placer connectivity by the transpiler/platform one.")])

    @patch("qililab.digital.circuit_router.logger.warning")
    def test_build_router(self, mock_logger_warning):
        """Test the _build_router method."""

        # Test default router (Sabre)
        router = self.circuit_router._build_router(None, linear_topology)
        assert isinstance(router, Sabre)
        assert router.connectivity == linear_topology

        # Test StarConnectivityRouter
        router = self.circuit_router._build_router(StarConnectivityRouter, star_topology)
        assert isinstance(router, StarConnectivityRouter)
        assert router.middle_qubit == 0
        assert  hasattr(router, "connectivity") == False

        # Test Sabre router with kwargs
        router = self.circuit_router._build_router((Sabre, {"lookahead": 2}), linear_topology)
        assert isinstance(router, Sabre)
        assert router.connectivity == linear_topology
        assert router.lookahead == 2

        # Test invalid router type
        with pytest.raises(TypeError, match="`router` arg"):
            self.circuit_router._build_router("invalid_router", linear_topology)

        # Test Router instance, instead of subclass
        sabre_instance = Sabre(linear_topology)
        mock_logger_warning.reset_mock()
        router = self.circuit_router._build_router(sabre_instance, linear_topology)
        assert isinstance(router, Sabre)
        assert router.connectivity == linear_topology
        mock_logger_warning.assert_has_calls([call("Substituting the router connectivity by the transpiler/platform one.")])


        star_router_instance = StarConnectivityRouter(star_topology)
        mock_logger_warning.reset_mock()
        router = self.circuit_router._build_router(star_router_instance, star_topology)
        assert isinstance(router, StarConnectivityRouter)
        assert router.middle_qubit == 0
        assert  hasattr(router, "connectivity") == False
        mock_logger_warning.assert_has_calls([call("Substituting the router connectivity by the transpiler/platform one.")])

        # Test Router instance, with kwargs:
        sabre_instance = Sabre(linear_topology, lookahead=2)
        router_kwargs = {"lookahead": 3}
        mock_logger_warning.reset_mock()
        router = self.circuit_router._build_router((sabre_instance,router_kwargs), linear_topology)
        assert router.lookahead == 2
        mock_logger_warning.assert_has_calls([call("Ignoring router kwargs, as the router is already an instance."),
            call("Substituting the router connectivity by the transpiler/platform one.")])

    def test_check_reverse_traversal_routing_connectivity(self):
        """Test the _check_ReverseTraversal_routing_connectivity method."""
        # Test for a linear topology
        og_placer = ReverseTraversal
        og_kwargs = {"routing_algorithm": Sabre}
        router = Sabre

        # Check with placer and routing algorithm both subclasses
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, linear_topology, router)
        assert (placer, kwargs) == (og_placer, og_kwargs)

        # Test for a weird router of the reversal
        og_kwargs = {"routing_algorithm": int, "lookahead": 2}
        with pytest.raises(TypeError, match=re.escape("`routing_algorithm` `Placer` kwarg (<class 'int'>) must be a `Router` subclass or instance, in `execute()`, `compile()`, `transpile_circuit()` or `route_circuit()`.")):
            self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, star_topology, router)

        # Test that the routing_algorithm get automatically inserted:
        og_kwargs = {"lookahead": 2}
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, linear_topology, router)
        assert (placer, kwargs) == (og_placer, og_kwargs | {"routing_algorithm": router})

        # Test instance of Router, change to chips topology:
        og_kwargs = {"routing_algorithm": Sabre(connectivity=None)}
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, linear_topology, router)
        og_kwargs["routing_algorithm"].connectivity = linear_topology
        assert (placer, kwargs) == (og_placer, og_kwargs)

        # Test subclass of Router, change to chips topology:
        og_kwargs = {"routing_algorithm": Sabre(connectivity=None)}
        og_placer = ReverseTraversal(connectivity=linear_topology, routing_algorithm=og_kwargs["routing_algorithm"])
        placer, kwargs = self.circuit_router._check_ReverseTraversal_routing_connectivity(og_placer, og_kwargs, linear_topology, router)
        assert og_placer.routing_algorithm.connectivity == linear_topology
        assert (placer, kwargs) == (og_placer, og_kwargs)
