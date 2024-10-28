
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
