import pytest
from qibo import gates
from qibo.models.circuit import Circuit as QiboCircuit

from qililab import __version__
from qililab.circuit import Circuit
from qililab.circuit.converters import QiboConverter
from qililab.circuit.operations import Measure, Wait, X


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


@pytest.fixture(name="simple_qibo_circuit")
def fixture_simple_qibo_circuit() -> QiboCircuit:
    """Return the Qibo version of simple circuit"""
    circuit = QiboCircuit(2)
    circuit.add(gates.X(0))
    circuit.add(gates.X(0))
    circuit.add(gates.X(1))
    circuit.add(gates.M(0, 1))
    return circuit


class TestQiboConverter:
    """Unit tests checking the QiliQasmConverter methods"""

    def test_to_qibo_method(self, simple_circuit: Circuit, simple_qibo_circuit: QiboCircuit):
        converter = QiboConverter()
        qibo_circuit = converter.to_qibo(simple_circuit)
        assert isinstance(qibo_circuit, QiboCircuit)
        assert qibo_circuit.nqubits == simple_qibo_circuit.nqubits

    def test_from_qibo_method(self, simple_circuit: Circuit, simple_qibo_circuit: QiboCircuit):
        converter = QiboConverter()
        circuit = converter.from_qibo(simple_qibo_circuit)
        assert isinstance(circuit, Circuit)
        assert circuit.num_qubits == simple_circuit.num_qubits
