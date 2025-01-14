import re
from unittest.mock import patch
import numpy as np
from qibo import Circuit, gates
import pytest

from qililab.digital.circuit_optimizer import CircuitOptimizer
from qililab.digital.native_gates import Drag


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
        optimized_gates = optimizer.optimize_gates(circuit.queue)

        # Check that the circuit is optimized
        assert len(optimized_gates) == 5
        # Check name attribute:
        assert [gate.name for gate in optimized_gates] == ["cx", "h", "drag", "h", "cx"]
        # CHeck the type of the gates:
        assert [type(gate).__name__ for gate in optimized_gates] == ["CNOT", "H", "Drag", "H", "CNOT"]
        # Assert the initial arguments:
        assert [gate.init_args for gate in optimized_gates] == [[2,3], [3], [3], [3], [2,3]]
        assert [gate.init_kwargs for gate in optimized_gates] == [{}, {}, {"theta": 2*np.pi, "phase": np.pi, "trainable": True}, {}, {}]


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
        optimized_gates = optimizer.optimize_gates(circuit)

        mock_cancelation.assert_called_once_with(circuit)
        assert len(optimized_gates) == 2
        assert [gate.name for gate in optimized_gates] == ["cz", "drag"]
        assert [type(gate).__name__ for gate in optimized_gates] == ["CZ", "Drag"]


    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer._create_circuit_gate_list", return_value=Circuit(5).queue)
    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer._sweep_circuit_cancelling_pairs_of_hermitian_gates", return_value=[("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer._get_circuit_gates", return_value=[("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
    def test_cancel_pairs_of_hermitian_gates(self, mock_get_circuit_gates, mock_sweep_circuit, mock_create_circuit):
        """Test run gate cancellations with mocks."""
        circuit = Circuit(2)
        circuit.add(gates.RZ(0, theta=np.pi / 2))
        circuit.add(gates.CZ(0, 1))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))

        optimizer = CircuitOptimizer(None)
        _ = optimizer.cancel_pairs_of_hermitian_gates(circuit.queue)

        mock_get_circuit_gates.assert_called_once_with(circuit.queue)
        mock_sweep_circuit.assert_called_once_with([("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
        mock_create_circuit.assert_called_once_with([("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])


    def test_get_circuit_gates(self):
        """Test get circuit gates."""
        circuit = Circuit(2)
        circuit.add(gates.X(0))
        circuit.add(gates.H(1))

        gates_list = CircuitOptimizer._get_circuit_gates(circuit.queue)

        assert gates_list == [("X", [0], {}), ("H", [1], {})]

    def test_create_gate(self):
        """Test create gate."""
        gate = CircuitOptimizer._create_gate("X", [0], {})
        assert isinstance(gate, gates.X)
        assert gate.init_args == [0]

    def test_create_circuit(self):
        """Test create circuit."""
        gates_list = [("X", [0], {}), ("H", [1], {})]
        circuit_list = CircuitOptimizer._create_circuit_gate_list(gates_list)

        assert len(circuit_list) == 2
        assert [gate.name for gate in circuit_list] == ["x", "h"]

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

    def test_merge_consecutive_drags_diff_qubits(self):
        """Test merge drag gates, with incorrect input."""
        drag_1 = Drag(0, theta=np.pi, phase=np.pi / 2)
        drag_2 = Drag(1, theta=np.pi, phase=np.pi / 2)

        optimizer = CircuitOptimizer(None)
        with pytest.raises(ValueError, match=re.escape("Cannot merge Drag gates acting on different qubits.")):
            _ = optimizer.merge_consecutive_drags(drag_1, drag_2, only_same_phi=True)

    def test_merge_consecutive_drags_same_phis(self):
        """Test merge drag gates."""
        drag_1 = Drag(0, theta=np.pi, phase=np.pi / 2)
        drag_2 = Drag(0, theta=np.pi, phase=np.pi / 2)

        optimizer = CircuitOptimizer(None)
        final_drag = optimizer.merge_consecutive_drags(drag_1, drag_2, only_same_phi=True)

        assert isinstance(final_drag, Drag)
        assert final_drag.parameters == (2 * np.pi, np.pi / 2)

    def test_merge_consecutive_drags_diff_phis(self):
        """Test merge drag gates."""
        drag_1 = Drag(0, theta=np.pi, phase=np.pi / 2)
        drag_2 = Drag(0, theta=np.pi, phase=np.pi)

        optimizer = CircuitOptimizer(None)
        final_drag = optimizer.merge_consecutive_drags(drag_1, drag_2, only_same_phi=False)

        assert final_drag is None


    def test_bunch_drag_gates_only_same_phis(self):
        """Test bunch drag gates."""
        circuit = Circuit(2)
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(1, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(1, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi))
        circuit.add(gates.RX(1, theta=np.pi / 2))
        circuit.add(Drag(1, theta=np.pi, phase=np.pi / 2))


        optimizer = CircuitOptimizer(None)
        gate_list = optimizer.bunch_drag_gates(circuit.queue, only_same_phi=True)

        assert len(gate_list) == 5

        assert isinstance(gate_list[0], Drag)
        assert gate_list[0].parameters == (3 * np.pi, np.pi / 2)

        assert isinstance(gate_list[1], Drag)
        assert gate_list[1].parameters == (2 * np.pi, np.pi / 2)

        assert isinstance(gate_list[2], Drag)
        assert gate_list[2].parameters == (np.pi, np.pi)

        assert isinstance(gate_list[3], gates.RX)

        assert isinstance(gate_list[4], Drag)
        assert gate_list[4].parameters == (np.pi, np.pi / 2)

    def test_bunch_drag_gates_diff_phis(self):
        """Test bunch drag gates."""
        circuit = Circuit(2)
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi))

        optimizer = CircuitOptimizer(None)
        gate_list = optimizer.bunch_drag_gates(circuit.queue, only_same_phi=True)

        assert gate_list == circuit.queue

    def test_delete_gates_with_no_amplitude(self):
        """Test delete gates with no amplitude."""
        circuit = Circuit(2)
        circuit.add(Drag(0, theta=0, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))

        gate_list = CircuitOptimizer.delete_gates_with_no_amplitude(circuit.queue)

        assert len(gate_list) == 1
        assert isinstance(gate_list[0], Drag)
        assert gate_list[0].parameters == (np.pi, np.pi / 2)

    def test_normalize_angles_of_drags(self):
        """Test normalize angles of drags."""
        circuit = Circuit(2)
        circuit.add(Drag(0, theta=3 * np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=2 * np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=2*np.pi))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))

        gate_list = CircuitOptimizer.normalize_angles_of_drags(circuit.queue)

        assert len(gate_list) == 6
        assert [gate.parameters for gate in gate_list] == [
            (np.pi, np.pi / 2),
            (0, np.pi / 2),
            (np.pi, 0),
            (np.pi, np.pi / 2),
            (np.pi, np.pi / 2),
            (np.pi, np.pi / 2),
        ]

    def test_normalize_angle(self):
        """Test normalize angle."""
        assert CircuitOptimizer._normalize_angle(3 * np.pi) == np.pi
        assert CircuitOptimizer._normalize_angle(2 * np.pi) == 0
        assert CircuitOptimizer._normalize_angle(3/2 * np.pi) == - np.pi/2
        assert CircuitOptimizer._normalize_angle(np.pi) == np.pi
        assert CircuitOptimizer._normalize_angle(np.pi / 2) == np.pi / 2
