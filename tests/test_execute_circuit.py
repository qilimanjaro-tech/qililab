"""Test execute script"""
from unittest.mock import MagicMock, patch

from qibo.gates import CNOT, RY, H, M, X
from qibo.models import Circuit

import qililab as ql

mock_platform = MagicMock()


class TestExecute:
    """Test execute method in the `execute.py` script"""

    @patch("qililab.execute_circuit.build_platform", return_value=mock_platform)
    def test_execute(self, mock_build: MagicMock):
        n_qubits = 5
        circuit = Circuit(n_qubits)
        circuit.add([X(1), H(2), RY(0, 2), CNOT(4, 1), X(4), H(3), M(*range(5))])
        runcard = "galadriel.yml"
        ql.execute(circuit, runcard)
        mock_build.assert_called_with(runcard="galadriel.yml")
        mock_platform.connect.assert_called_once_with()
        mock_platform.initial_setup.assert_called_once_with()
        mock_platform.turn_on_instruments.assert_called_once_with()
        mock_platform.execute.assert_called_once_with(circuit, num_avg=1, repetition_duration=200_000, num_bins=1)
        mock_platform.disconnect.assert_called_once_with()
