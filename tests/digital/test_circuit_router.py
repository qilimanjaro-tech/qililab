import re
from unittest.mock import call, patch
import pytest
import networkx as nx
from qibo import Circuit, gates
from qililab.digital.routing.algorithms import Preprocessing

from qililab.digital.routing.algorithms import ReverseTraversal, StarConnectivityPlacer, Sabre, StarConnectivityRouter

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
circuit_test = Circuit(5)
circuit_test.add(gates.H(0))
# Tests circuit with SWAP
circuit_w_swap_test = Circuit(5)
circuit_test.add(gates.H(0))
circuit_w_swap_test.add(gates.SWAP(0,1))
# Tests layouts
qibo_test_layout, test_layout = {1:0, 0:1}, [1, 0]
qibo_test_bad_layout = {0:0, 1:0}

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
            assert router.placer.middle_qubit is None
        if type in ["linear", "star"]:
            assert router.connectivity == topology
            assert isinstance(router.preprocessing, Preprocessing)

    def test_route_doesnt_affect_already_routed_circuit(self):
        """Test the routing of a circuit"""
        routed_circuit, final_layout = CircuitRouter(linear_topology).route(linear_circuit)

        assert final_layout == [0, 1, 2, 3, 4]
        assert routed_circuit.nqubits == linear_circuit.nqubits
        assert routed_circuit.depth == linear_circuit.depth
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] == [(gate.name, gate.qubits)  for gate in linear_circuit.queue]

    def test_route_affects_non_routed_circuit(self):
        """Test the routing of a circuit"""

        routed_circuit, final_layout = CircuitRouter(star_topology).route(linear_circuit)

        # Assert that the circuit was routed:
        assert final_layout != [0, 1, 2, 3, 4]
        assert routed_circuit.nqubits == linear_circuit.nqubits
        assert routed_circuit.depth > linear_circuit.depth
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] != [(gate.name, gate.qubits)  for gate in linear_circuit.queue]
        assert {gate.name for gate in routed_circuit.queue} >= {gate.name for gate in linear_circuit.queue} # Assert more gates


##################
### UNIT TESTS ###
##################
class TestCircuitRouterUnit:
    """Tests for the circuit router class, unit tests."""

    circuit_router = CircuitRouter(linear_topology)

    @pytest.mark.parametrize(
        "type, circuit, layout, least_swaps",
        [
            ("good", circuit_test, test_layout, 0),
            ("none_swaps", circuit_test, test_layout, None),
        ]
    )
    @patch("qililab.config.logger.info")
    @patch("qililab.digital.circuit_router.CircuitRouter._iterate_routing")
    def test_route(self, mock_iterate, mock_logger_info, type, circuit, layout, least_swaps):
        """Test the routing of a circuit."""
        # Set the mock returns to the parametrized test values:
        mock_iterate.return_value = (circuit, least_swaps, layout)

        # Execute the routing:
        if type in ["good", "none_swaps"]:
            routed_circuit, final_layout = self.circuit_router.route(linear_circuit)
            # Assert you return the same outputs as the mocked _iterate_routing
            assert (routed_circuit, final_layout) ==(circuit_test, test_layout)

        # Assert that the logger is called properly
        if type == "good":
            mock_logger_info.assert_has_calls([
                call("The best found routing, has 0 swaps."),
                call(f"{routed_circuit.wire_names}: Initial Re-mapping of the Original Logical Qubits (l_q), in the Physical Circuit: [l_q in wire 0, l_q in wire 1, ...]."),
                call(f"{final_layout}: Final Re-mapping (Initial + SWAPs routing) of the Original Logical Qubits (l_q), in the Physical Circuit: [l_q in wire 0, l_q in wire 1, ...].")
            ])
        elif type == "none_swaps":
            mock_logger_info.assert_called_once_with("No routing was done. Most probably due to routing iterations being 0.")

        # Assert that the routing pipeline was called with the correct arguments
        mock_iterate.assert_called_once_with(self.circuit_router.pipeline, linear_circuit, 10)

    @pytest.mark.parametrize("type, qibo_layout, layout", [("good", qibo_test_layout, test_layout), ("bad_layout", qibo_test_bad_layout, None)])
    def test_get_logical_qubit_of_each_wire(self, type, qibo_layout, layout):
        if type == "bad_layout":
            with pytest.raises(ValueError, match=re.escape(f"The final layout: {qibo_test_bad_layout} is not valid. i.e. a logical qubit is mapped to more than one physical qubit, or a key/value isn't a number. Try again, if the problem persists, try another placer/routing algorithm.")):
                _ = self.circuit_router._get_logical_qubit_of_each_wire(qibo_layout)

        elif type == "good":
            new_layout_format = self.circuit_router._get_logical_qubit_of_each_wire(qibo_layout)
            assert new_layout_format == layout

    @pytest.mark.parametrize(
        "type, circuit, qibo_layout, layout, least_swaps, iterations",
        [
            ("without_swaps", circuit_test, qibo_test_layout, test_layout, None, 10),
            ("with_swaps", circuit_w_swap_test, qibo_test_layout, test_layout, 1, 7),

        ]
    )
    @patch("qililab.digital.circuit_router.CircuitRouter._apply_initial_remap")
    @patch("qililab.digital.circuit_router.CircuitOptimizer.remove_redundant_start_controlled_gates")
    @patch("qililab.digital.circuit_router.Passes.__call__")
    def test_iterate_routing_with_and_without_swaps(self, mock_qibo_routing, mock_removing_swaps, mock_apply_initial_remap, type, circuit, qibo_layout, layout, least_swaps, iterations):
        """ Test the iterate routing of a circuit, with and without swaps."""
        # Add the mock return value to the parametrized test values:
        mock_qibo_routing.return_value = (circuit, qibo_layout)
        mock_removing_swaps.return_value = circuit
        mock_apply_initial_remap.return_value = circuit

        # Execute the iterate_routing:
        routed_circuit, least_swaps, final_layout = self.circuit_router._iterate_routing(self.circuit_router.pipeline, circuit, iterations)

        # Assert calls on the routing algorithm:
        if type == "with_swaps":
            # Assert called as many times as number of iterations, since there are swaps present:
            mock_qibo_routing.assert_has_calls([call(circuit)]*iterations)
            mock_removing_swaps.assert_has_calls([call(circuit, gates.SWAP)]*iterations)
            expected_least_swaps = 1
        elif type == "without_swaps":
            # Assert only called once, since there are no swaps:
            mock_qibo_routing.assert_called_once_with(circuit)
            mock_removing_swaps.assert_called_once_with(circuit, gates.SWAP)
            expected_least_swaps = iterations = 0 # Since there are no swaps, no iterations have been needed

        # Assert you return the correct outputs:
        assert (routed_circuit, least_swaps, final_layout) == (circuit, expected_least_swaps, layout)

    def test_if_star_algorithms_for_nonstar_connectivity(self):
        """Test the routing of a circuit"""
        circ_router = self.circuit_router

        # Assert cases where it needs to return True
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, StarConnectivityPlacer(), circ_router.router)
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, ReverseTraversal(circ_router.router), StarConnectivityRouter())
        assert True == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, StarConnectivityPlacer(), StarConnectivityRouter())

        # Assert cases where it needs to return False
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(linear_topology, ReverseTraversal(circ_router.router), circ_router.router)
        assert False == circ_router._if_star_algorithms_for_nonstar_connectivity(star_topology, ReverseTraversal(circ_router.router), StarConnectivityRouter())
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
        assert not self.circuit_router._if_layout_is_not_valid(qibo_test_layout)

        # Test invalid layout
        assert self.circuit_router._if_layout_is_not_valid(qibo_test_bad_layout)

    @patch("qililab.digital.circuit_router.CircuitRouter._check_ReverseTraversal_routing_connectivity")
    @patch("qililab.digital.circuit_router.logger.warning")
    def test_build_placer(self, mock_logger_warning, mock_check_reverse):
        """Test the _build_placer method."""
        mock_check_reverse.return_value = (ReverseTraversal, {"routing_algorithm": self.circuit_router.router})

        # Test default placer (ReverseTraversal)
        placer = self.circuit_router._build_placer(None, self.circuit_router.router, linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (linear_topology, self.circuit_router.router)

        # Test ReverseTraversal placer
        placer = self.circuit_router._build_placer(ReverseTraversal, self.circuit_router.router, linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert placer.connectivity == linear_topology
        assert hasattr(placer, "routing_algorithm") == True

        # Test StarConnectivityPlacer
        placer = self.circuit_router._build_placer(StarConnectivityPlacer, self.circuit_router.router, star_topology)
        assert isinstance(placer, StarConnectivityPlacer)
        assert placer.middle_qubit is None
        assert hasattr(placer, "routing_algorithm") is False
        assert hasattr(placer, "connectivity") is True

        # Test ReverseTraversal with kwargs
        mock_check_reverse.reset_mock()
        placer = self.circuit_router._build_placer((ReverseTraversal, {"routing_algorithm": self.circuit_router.router}), self.circuit_router.router, linear_topology)
        mock_check_reverse.assert_called_once_with(ReverseTraversal, {"routing_algorithm": self.circuit_router.router}, linear_topology, self.circuit_router.router)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (linear_topology, self.circuit_router.router)

        # Test invalid placer type
        with pytest.raises(TypeError, match="`placer` arg"):
            self.circuit_router._build_placer("invalid_placer", self.circuit_router.router, linear_topology)

        # Test Placer instance, instead than subclass:
        reverse_placer_instance = ReverseTraversal(self.circuit_router.router, linear_topology)
        mock_logger_warning.reset_mock()
        placer = self.circuit_router._build_placer(reverse_placer_instance, self.circuit_router.router, linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert placer.connectivity == linear_topology
        assert hasattr(placer, "routing_algorithm") == True
        # No call to warning, cause checking of Reverse is mocked.

        star_placer_instance = StarConnectivityPlacer(star_topology)
        mock_logger_warning.reset_mock()
        placer = self.circuit_router._build_placer(star_placer_instance, self.circuit_router.router, star_topology)
        assert isinstance(placer, StarConnectivityPlacer)
        assert placer.middle_qubit is None
        assert hasattr(placer, "routing_algorithm") is False
        assert hasattr(placer, "connectivity") == True
        mock_logger_warning.assert_called_once_with("Substituting the placer connectivity by the transpiler/platform/coupling_map one.")

        reverse_traversal_instance = ReverseTraversal(self.circuit_router.router, connectivity=linear_topology)
        placer = self.circuit_router._build_placer(reverse_traversal_instance, self.circuit_router.router, linear_topology)
        assert isinstance(placer, ReverseTraversal)
        assert (placer.connectivity, placer.routing_algorithm) == (linear_topology, self.circuit_router.router)

        # Test Placer instance, with kwargs:
        placer_instance = StarConnectivityPlacer()
        placer_kwargs = {"connectivity": 1}
        mock_logger_warning.reset_mock()
        router = self.circuit_router._build_placer((placer_instance,placer_kwargs),self.circuit_router.router, linear_topology)
        assert hasattr(router, "lookahead") == False
        mock_logger_warning.assert_has_calls([
            call("Ignoring placer kwargs, as the placer is already an instance."),
            call("Substituting the placer connectivity by the transpiler/platform/coupling_map one.")
        ])

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
        assert router.middle_qubit is None
        assert router.connectivity == star_topology

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
        mock_logger_warning.assert_has_calls([call("Substituting the router connectivity by the transpiler/platform/coupling_map one.")])


        star_router_instance = StarConnectivityRouter(star_topology)
        mock_logger_warning.reset_mock()
        router = self.circuit_router._build_router(star_router_instance, star_topology)
        assert isinstance(router, StarConnectivityRouter)
        assert router.middle_qubit is None
        assert router.connectivity == star_topology
        mock_logger_warning.assert_has_calls([call("Substituting the router connectivity by the transpiler/platform/coupling_map one.")])

        # Test Router instance, with kwargs:
        sabre_instance = Sabre(linear_topology, lookahead=2)
        router_kwargs = {"lookahead": 3}
        mock_logger_warning.reset_mock()
        router = self.circuit_router._build_router((sabre_instance,router_kwargs), linear_topology)
        assert router.lookahead == 2
        mock_logger_warning.assert_has_calls([call("Ignoring router kwargs, as the router is already an instance."),
            call("Substituting the router connectivity by the transpiler/platform/coupling_map one.")])

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
