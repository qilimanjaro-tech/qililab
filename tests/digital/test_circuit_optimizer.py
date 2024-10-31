from unittest.mock import patch
import numpy as np
from qibo import Circuit, gates

from qililab.digital.circuit_optimizer import CircuitOptimizer
from qililab.digital.native_gates import Drag
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings


class TestCircuitOptimizerIntegration:
    """Tests for the circuit optimizer class, with integration tests."""

    def test_run_gate_cancelation(self):
        """Test run gate cancelation."""
        # Create a circuit with two gates that cancel each other.
        circuit = Circuit(5)

        # pairs that cancels:
        circuit.add(gates.H(0))
        circuit.add(gates.H(0))

        # From here only the X(4) will cancel with the X(4) at the end.
        circuit.add(gates.CNOT(2,3)) # 1
        circuit.add(gates.X(4))
        circuit.add(gates.H(3)) # 2

        # The 0-1 and 1-4 CNOTs shold cancel each other.
        circuit.add(gates.CNOT(1,4))
        circuit.add(gates.CNOT(0,1))
        circuit.add(Drag(3, theta=2*np.pi, phase=np.pi)) # 3
        circuit.add(gates.CNOT(0,1))
        circuit.add(gates.CNOT(1,4))

        circuit.add(gates.H(3)) # 4
        circuit.add(gates.X(4))
        circuit.add(gates.CNOT(2,3)) # 5


        # Optimize the circuit.
        optimizer = CircuitOptimizer(None)
        optimized_circuit = optimizer.run_gate_cancellations(circuit)

        # Check that the circuit is optimized
        assert len(optimized_circuit.queue) == 5
        # Check name attribute:
        assert [gate.name for gate in optimized_circuit.queue] == ["cx", "h", "drag", "h", "cx"]
        # CHeck the type of the gates:
        assert [type(gate).__name__ for gate in optimized_circuit.queue] == ["CNOT", "H", "Drag", "H", "CNOT"]
        # Assert the initial arguments:
        assert [gate.init_args for gate in optimized_circuit.queue] == [[2,3], [3], [3], [3], [2,3]]
        assert [gate.init_kwargs for gate in optimized_circuit.queue] == [{}, {}, {"theta": 2*np.pi, "phase": np.pi, "trainable": True}, {}, {}]


class TestCircuitOptimizerUnit:
    """Tests for the circuit optimizer class, with Unit test."""

    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer.cancel_pairs_of_hermitian_gates", return_value=[gates.CZ(0, 1), Drag(0, theta=np.pi, phase=np.pi / 2)])
    def test_run_gate_cancellations(self, mock_cancelation):
        """Test optimize transpilation."""
        circuit = Circuit(2)
        circuit.add(gates.RZ(0, theta=np.pi / 2))
        circuit.add(gates.CZ(0, 1))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))

        optimizer = CircuitOptimizer(None)
        optimized_gates = optimizer.run_gate_cancellations(circuit)

        mock_cancelation.assert_called_once_with(circuit)
        assert len(optimized_gates) == 2
        assert [gate.name for gate in optimized_gates] == ["cz", "drag"]
        assert [type(gate).__name__ for gate in optimized_gates] == ["CZ", "Drag"]


    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer._create_circuit", return_value=[gates.CZ(0, 1), Drag(0, theta=np.pi, phase=np.pi / 2)])
    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer._sweep_circuit_cancelling_pairs_of_hermitian_gates", return_value=[gates.CZ(0, 1), Drag(0, theta=np.pi, phase=np.pi / 2)])
    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer._get_circuit_gates", return_value=[("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
    def test_run_gate_cancellations_with_mocks(self, mock_get_circuit_gates, mock_sweep_circuit, mock_create_circuit):
        """Test run gate cancellations with mocks."""
        circuit = Circuit(2)
        circuit.add(gates.RZ(0, theta=np.pi / 2))
        circuit.add(gates.CZ(0, 1))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))

        optimizer = CircuitOptimizer(None)
        optimized_circuit = optimizer.cancel_pairs_of_hermitian_gates(circuit)

        mock_get_circuit_gates.assert_called_once_with(circuit)
        mock_sweep_circuit.assert_called_once_with([("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
        mock_create_circuit.assert_called_once_with([("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})], circuit.nqubits)

        assert len(optimized_circuit) == 2
        assert [gate.name for gate in optimized_circuit] == ["cz", "drag"]
        assert [type(gate).__name__ for gate in optimized_circuit] == ["CZ", "Drag"]


    def test_get_circuit_gates(self):
        """Test get circuit gates."""
        circuit = Circuit(2)
        circuit.add(gates.X(0))
        circuit.add(gates.H(1))

        gates_list = CircuitOptimizer._get_circuit_gates(circuit)

        assert gates_list == [("X", [0], {}), ("H", [1], {})]

    def test_create_gate(self):
        """Test create gate."""
        gate = CircuitOptimizer._create_gate("X", [0], {})
        assert isinstance(gate, gates.X)
        assert gate.init_args == [0]

    def test_create_circuit(self):
        """Test create circuit."""
        gates_list = [("X", [0], {}), ("H", [1], {})]
        circuit = CircuitOptimizer._create_circuit(gates_list, 2)

        assert len(circuit.queue) == 2
        assert [gate.name for gate in circuit.queue] == ["x", "h"]

    def test_sweep_circuit_cancelling_pairs_of_hermitian_gates(self):
        """Test sweep circuit cancelling pairs of hermitian gates."""
        circ_list = [("X", [0], {}), ("X", [0], {}), ("H", [1], {}), ("H", [1], {})]
        output_circ_list = CircuitOptimizer._sweep_circuit_cancelling_pairs_of_hermitian_gates(circ_list)

        assert output_circ_list == []

    def test_extract_qubits(self):
        """Test extract qubits."""
        qubits = CircuitOptimizer._extract_qubits([0, 1])
        assert qubits == [0, 1]

        qubits = CircuitOptimizer._extract_qubits(0)
        assert qubits == [0]
