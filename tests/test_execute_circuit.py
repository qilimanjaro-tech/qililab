"""Test execute script"""
from unittest.mock import MagicMock, patch

import pytest
from qibo.gates import CNOT, RY, H, M, X
from qibo.models import Circuit

import qililab as ql


class TestExecute:
    """Test execute method in the `execute.py` script"""

    def test_execute(self):
        n_qubits = 5
        circuit = Circuit(n_qubits)
        circuit.add([X(1), H(2), RY(0, 2), CNOT(4, 1), X(4), H(3), M(*range(5))])
        runcard = "galadriel.yml"
        mock_platform = MagicMock()
        with patch("qililab.execute_circuit.build_platform", return_value=mock_platform) as mock_build:
            results = ql.execute(circuit, runcard)
            assert isinstance(results, MagicMock)
            mock_build.assert_called_with(runcard="galadriel.yml")
        mock_platform.connect.assert_called_once_with()
        mock_platform.initial_setup.assert_called_once_with()
        mock_platform.turn_on_instruments.assert_called_once_with()
        mock_platform.execute.assert_called_once()
        mock_platform.disconnect.assert_called_once_with()

    def test_execute_calls_disconnect_after_error(self):
        n_qubits = 5
        circuit = Circuit(n_qubits)
        circuit.add([X(1), H(2), RY(0, 2), CNOT(4, 1), X(4), H(3), M(*range(5))])
        runcard = "galadriel.yml"
        with pytest.raises(Exception):
            mock_platform = MagicMock()
            mock_platform.turn_on_instruments.side_effect = Exception()
            with patch("qililab.execute_circuit.build_platform", return_value=mock_platform) as mock_build:
                ql.execute(circuit, runcard)
            mock_build.assert_called_with(runcard="galadriel.yml")
            mock_platform.connect.assert_called_once_with()
            mock_platform.initial_setup.assert_called_once_with()
            mock_platform.turn_on_instruments.assert_called_once_with()
            mock_platform.execute.assert_not_called()
            mock_platform.disconnect.assert_called_once_with()

    def test_execute_circuit_with_multiple_circuits(self):
        """Test that executing a list of circuits returns a list of results."""
        n_qubits = 5
        circuit = Circuit(n_qubits)
        circuit.add([X(1), H(2), RY(0, 2), CNOT(4, 1), X(4), H(3), M(*range(5))])
        runcard = "galadriel.yml"
        mock_platform = MagicMock()
        with patch("qililab.execute_circuit.build_platform", return_value=mock_platform) as mock_build:
            results = ql.execute([circuit, circuit], runcard)
            assert isinstance(results, list)
            mock_build.assert_called_with(runcard="galadriel.yml")
        mock_platform.connect.assert_called_once_with()
        mock_platform.initial_setup.assert_called_once_with()
        mock_platform.turn_on_instruments.assert_called_once_with()
        assert mock_platform.execute.call_count == 2
        mock_platform.disconnect.assert_called_once_with()
