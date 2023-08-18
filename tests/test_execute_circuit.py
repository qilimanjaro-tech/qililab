"""Test execute script"""
from unittest.mock import MagicMock, patch

from qibo.gates import CNOT, RY, H, M, X
from qibo.models import Circuit

import qililab as ql


class TestExecute:
    """Test execute method in the `execute.py` script"""

    @patch("qililab.experiment.experiment.Experiment.execute")
    @patch("qililab.execute_circuit.build_platform")
    def test_execute(self, mock_build: MagicMock, mock_execute: MagicMock):
        n_qubits = 5
        circuit = Circuit(n_qubits)
        circuit.add([X(1), H(2), RY(0, 2), CNOT(4, 1), X(4), H(3), M(*range(5))])
        runcard = "galadriel.yml"
        ql.execute(circuit, runcard)
        mock_build.assert_called_with(path="galadriel.yml")
        mock_execute.assert_called_once_with(save_experiment=False, save_results=False)
