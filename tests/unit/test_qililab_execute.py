"""Test execute script"""
from unittest.mock import MagicMock, patch

from qibo.gates import CNOT, RY, H, M, X
from qibo.models import Circuit

import qililab as ql


class TestExecute:
    """Test execute mehod in the `execute.py` script"""

    @patch("qililab.experiment.experiment.Experiment.execute")
    @patch("qililab.ExperimentOptions", autospec=True)
    @patch("qililab.ExperimentSettings", autospec=True)
    @patch("qililab.build_platform")
    @patch("qililab.translate_circuit")
    def test_execute(
        self,
        mock_translate_circuit: MagicMock,
        mock_build_platform: MagicMock,
        mock_settings: MagicMock,
        mock_options: MagicMock,
        mock_execute: MagicMock,
    ):
        n_qubits = 5
        circuit = Circuit(n_qubits)
        circuit.add([X(1), H(2), RY(0, 2), CNOT(4, 1), X(4), H(3), M(*range(5))])
        runcard = "galadriel"
        ql.execute(circuit, runcard)
        mock_translate_circuit.assert_called_with(circuit, optimize=True)
        mock_build_platform.assert_called_with(name=runcard)
        mock_settings.assert_called_once()
        mock_options.assert_called_once()
        mock_execute.assert_called_once()
