from copy import deepcopy
import re
from unittest.mock import patch
import numpy as np
from qibo import Circuit, gates
import pytest

from qililab.digital.circuit_optimizer import CircuitOptimizer
from qililab.digital.native_gates import Drag
from tests.data import Galadriel
from tests.test_utils import build_platform


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


        # Run Optimize the circuit.
        optimizer = CircuitOptimizer(None)
        optimized_gates_hermitian_cancel = optimizer.cancel_pairs_of_hermitian_gates(circuit.queue)
        optimized_gates_complete = optimizer.optimize_gates(circuit.queue)

        # Check that the circuit is optimized
        assert len(optimized_gates_hermitian_cancel) == 5
        assert len(optimized_gates_complete) == 4
        # Check name attribute:
        assert [gate.name for gate in optimized_gates_hermitian_cancel] == ["cx", "h", "drag", "h", "cx"]
        assert [gate.name for gate in optimized_gates_complete] == ["h", "drag", "h", "cx"]
        # CHeck the type of the gates:
        assert [type(gate).__name__ for gate in optimized_gates_hermitian_cancel] == ["CNOT", "H", "Drag", "H", "CNOT"]
        assert [type(gate).__name__ for gate in optimized_gates_complete] == ["H", "Drag", "H", "CNOT"]
        # Assert the initial arguments:
        assert [gate.init_args for gate in optimized_gates_hermitian_cancel] == [[2,3], [3], [3], [3], [2,3]]
        assert [gate.init_args for gate in optimized_gates_complete] == [[3], [3], [3], [2,3]]
        assert [gate.init_kwargs for gate in optimized_gates_hermitian_cancel] == [{}, {}, {"theta": 2*np.pi, "phase": np.pi, "trainable": True}, {}, {}]
        assert [gate.init_kwargs for gate in optimized_gates_complete] == [{}, {"theta": 2*np.pi, "phase": np.pi, "trainable": True}, {}, {}]


class TestCircuitOptimizerUnit:
    """Tests for the circuit optimizer class, with Unit test."""

    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer.cancel_pairs_of_hermitian_gates", return_value=[gates.CZ(0, 1), Drag(0, theta=np.pi, phase=np.pi / 2)])
    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer.remove_redundant_start_controlled_gates", return_value=[Drag(0, theta=np.pi, phase=np.pi / 2)])
    def test_run_gate_cancellations(self, mock_redundant_gates, mock_cancellation):
        """Test optimize transpilation."""
        circuit = Circuit(2)
        circuit.add(gates.RZ(0, theta=np.pi / 2))
        circuit.add(gates.CZ(0, 1))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))

        optimizer = CircuitOptimizer(None)
        optimized_gates_complete = optimizer.optimize_gates(circuit.queue)
        mock_cancellation.assert_called_once_with(circuit.queue)
        mock_redundant_gates.assert_called_once_with(mock_cancellation.return_value)

        # Assert remaining gates:
        assert len(optimized_gates_complete) == 1
        assert [gate.name for gate in optimized_gates_complete] == ["drag"]
        assert [type(gate).__name__ for gate in optimized_gates_complete] == ["Drag"]


    @patch("qililab.digital.native_gates._GateHandler.create_qibo_gates_from_gates_info", return_value=Circuit(5).queue)
    @patch("qililab.digital.circuit_optimizer.CircuitOptimizer._sweep_circuit_cancelling_pairs_of_hermitian_gates", return_value=[("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
    @patch("qililab.digital.native_gates._GateHandler.get_circuit_gates_info", return_value=[("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
    def test_cancel_pairs_of_hermitian_gates(self, mock_get_circuit_gates_info, mock_sweep_circuit, mock_create_circuit):
        """Test run gate cancellations with mocks."""
        circuit = Circuit(2)
        circuit.add(gates.RZ(0, theta=np.pi / 2))
        circuit.add(gates.CZ(0, 1))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))

        optimizer = CircuitOptimizer(None)
        _ = optimizer.cancel_pairs_of_hermitian_gates(circuit.queue)

        mock_get_circuit_gates_info.assert_called_once_with(circuit.queue)
        mock_sweep_circuit.assert_called_once_with([("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])
        mock_create_circuit.assert_called_once_with([("CZ", [0, 1], {}), ("Drag", [0], {"theta": np.pi, "phase": np.pi / 2})])


    def test_sweep_circuit_cancelling_pairs_of_hermitian_gates(self):
        """Test sweep circuit cancelling pairs of hermitian gates."""
        circuit_gates = [("X", [0], {}), ("X", [0], {}), ("H", [1], {}), ("H", [1], {})]
        output_circuit_gates = CircuitOptimizer._sweep_circuit_cancelling_pairs_of_hermitian_gates(circuit_gates)

        assert output_circuit_gates == []


    def test_merge_consecutive_drags_diff_qubits(self):
        """Test merge drag gates, with incorrect input."""
        drag_1 = Drag(0, theta=np.pi, phase=np.pi / 2)
        drag_2 = Drag(1, theta=np.pi, phase=np.pi / 2)

        optimizer = CircuitOptimizer(None)
        with pytest.raises(ValueError, match=re.escape("Cannot merge Drag gates acting on different qubits.")):
            _ = optimizer.merge_consecutive_drags(drag_1, drag_2)

    def test_merge_consecutive_drags_same_phis(self):
        """Test merge drag gates."""
        drag_1 = Drag(0, theta=np.pi/2-0.1, phase=np.pi / 2)
        drag_2 = Drag(0, theta=np.pi/2, phase=np.pi / 2)

        optimizer = CircuitOptimizer(None)
        final_drag = optimizer.merge_consecutive_drags(drag_1, drag_2)

        assert isinstance(final_drag, Drag)
        assert final_drag.parameters == (np.pi-0.1, np.pi / 2)

    def test_merge_consecutive_drags_opposite_phis(self):
        """Test merge drag gates."""
        drag_1 = Drag(0, theta=np.pi/2+0.1, phase=(np.pi / 2)+0.1)
        drag_2 = Drag(0, theta=np.pi/2, phase=-(np.pi / 2)+0.1)

        optimizer = CircuitOptimizer(None)
        final_drag = optimizer.merge_consecutive_drags(drag_1, drag_2)

        assert isinstance(final_drag, Drag)
        assert np.isclose(final_drag.parameters, (0.1, (np.pi / 2)+0.1)).all()

    def test_merge_consecutive_drags_diff_phis(self):
        """Test merge drag gates."""
        drag_1 = Drag(0, theta=np.pi, phase=np.pi / 2)
        drag_2 = Drag(0, theta=np.pi, phase=np.pi)

        optimizer = CircuitOptimizer(None)
        final_drag = optimizer.merge_consecutive_drags(drag_1, drag_2)

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
        gate_list = optimizer.bunch_drag_gates(circuit.queue)

        assert len(gate_list) == 5

        assert isinstance(gate_list[0], Drag)
        assert gate_list[0].parameters == (np.pi, np.pi / 2)

        assert isinstance(gate_list[1], Drag)
        assert gate_list[1].parameters == (0, np.pi / 2)

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
        gate_list = optimizer.bunch_drag_gates(circuit.queue)

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

        ###########

    @pytest.mark.parametrize(
        "wire_names", [None, [0, 1]]
    )
    def test_make_gate_None_in_queue(self, wire_names):
        """Test make gate None in queue."""
        circuit = Circuit(2)
        circuit.add(gates.SWAP(0, 1))
        circuit.add(gates.X(0))

        queue = circuit.queue
        wire_names_was_None = not deepcopy(wire_names)

        CircuitOptimizer._make_gate_None_in_queue(queue[0], 0, queue, wire_names)

        assert queue[0] is None
        if wire_names_was_None:
            assert wire_names is None
        else:
            assert wire_names == [1, 0]


    def test_make_gate_None_in_queue_no_wire_names(self):
        """Test make gate None in queue."""
        circuit = Circuit(2)
        circuit.add(gates.SWAP(0, 1))
        circuit.add(gates.X(0))

        queue = circuit.queue
        wire_names = None

        CircuitOptimizer._make_gate_None_in_queue(queue[0], 0, queue, wire_names)

        assert queue[0] is None
        assert wire_names is None

    def test_remove_redundant_start_controlled_gates(self):
        """Test remove redundant start controlled gates."""
        circuit = Circuit(3)
        circuit.add(gates.CNOT(0, 1))
        circuit.add(gates.CNOT(1, 2))
        circuit.add(gates.H(0))
        circuit.add(gates.CNOT(0, 1))

        optimizer = CircuitOptimizer(None)
        optimized_circuit = optimizer.remove_redundant_start_controlled_gates(circuit)

        assert len(optimized_circuit.queue) == 2
        assert [gate.name for gate in optimized_circuit.queue] == ["h", "cx"]

    def test_add_phases_from_RZs_and_CZs_to_drags(self):
        """Test add phases from RZs and CZs to drags."""
        circuit = Circuit(2)
        circuit.add(gates.RZ(0, theta=np.pi / 2))
        circuit.add(gates.CZ(0, 1))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2)) # Should end up, with the phase cancelled by RZ and then a correction added by CZ.

        platform = build_platform(runcard=Galadriel.runcard)
        optimizer = CircuitOptimizer(platform.digital_compilation_settings)
        optimized_gates = optimizer.add_phases_from_RZs_and_CZs_to_drags(circuit.queue, 2)

        assert len(optimized_gates) == 2
        assert isinstance(optimized_gates[1], Drag)
        correction_from_CZ_in_qubit_0= platform.digital_compilation_settings.gates["CZ(0,1)"][0].pulse.options["q0_phase_correction"]
        assert np.isclose(optimized_gates[1].parameters, (np.pi, -correction_from_CZ_in_qubit_0)).all

    def test_optimize_transpiled_gates_all_cancels(self):
        """Test optimize transpiled gates."""
        circuit = Circuit(2)
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(1, theta=0, phase=np.pi / 2))

        optimizer = CircuitOptimizer(None)
        optimized_gates = optimizer.optimize_transpiled_gates(circuit.queue)

        assert len(optimized_gates) == 0

    def test_optimize_transpiled_gates(self):
        """Test optimize transpiled gates."""
        circuit = Circuit(2)
        circuit.add(Drag(0, theta=np.pi, phase=np.pi / 2))
        circuit.add(Drag(0, theta=np.pi/2, phase=np.pi / 2))
        circuit.add(Drag(1, theta=np.pi, phase=np.pi / 2))

        optimizer = CircuitOptimizer(None)
        optimized_gates = optimizer.optimize_transpiled_gates(circuit.queue)

        assert len(optimized_gates) == 2
        assert [gate.parameters for gate in optimized_gates] == [(-np.pi /2, np.pi / 2), (np.pi, np.pi / 2)]
