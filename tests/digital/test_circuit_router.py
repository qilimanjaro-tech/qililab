
import pytest
import networkx as nx
from qibo import Circuit, gates
from qibo.transpiler.optimizer import Preprocessing
from qibo.transpiler.pipeline import Passes
from qibo.transpiler.placer import Placer, ReverseTraversal, StarConnectivityPlacer
from qibo.transpiler.router import Router, Sabre, StarConnectivityRouter

from qililab.digital.circuit_router import CircuitRouter

linear_connectivity = [(0,1), (1,2), (2,3), (3,4)]
star_connectivity = [(0,1), (0,2), (0,3), (0,4)]

class TestCircuitRouter:
    """Tests for the circuit router class"""

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

    def test_route_doenst_affect_already_routed_circuit(self):
        """Test the routing of a circuit"""
        connectivity = nx.Graph(linear_connectivity)
        circuit_router = CircuitRouter(connectivity)

        circuit = Circuit(5)
        circuit.add(gates.H(0))
        circuit.add(gates.CNOT(0, 1))
        circuit.add(gates.CNOT(1, 2))
        circuit.add(gates.CNOT(2, 3))
        circuit.add(gates.CNOT(3, 4))

        routed_circuit, final_layout = circuit_router.route(circuit)

        assert final_layout == {"q0":0, "q1":1, "q2":2, "q3":3, "q4":4}
        assert routed_circuit.nqubits == 5
        assert routed_circuit.depth == 5
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] == [(gate.name, gate.qubits)  for gate in circuit.queue]

    def test_route_affects_non_routed_circuit(self):
        """Test the routing of a circuit"""
        connectivity = nx.Graph(star_connectivity)
        circuit_router = CircuitRouter(connectivity)

        circuit = Circuit(5)
        circuit.add(gates.H(0))
        circuit.add(gates.CNOT(0, 1))
        circuit.add(gates.CNOT(1, 2))
        circuit.add(gates.CNOT(2, 3))
        circuit.add(gates.CNOT(3, 4))

        routed_circuit, _ = circuit_router.route(circuit)
        assert routed_circuit.nqubits == 5
        assert routed_circuit.depth > 5
        assert [(gate.name, gate.qubits) for gate in routed_circuit.queue] != [(gate.name, gate.qubits)  for gate in circuit.queue]
        assert {gate.name for gate in routed_circuit.queue} >= {gate.name for gate in circuit.queue} # Assert more gates
