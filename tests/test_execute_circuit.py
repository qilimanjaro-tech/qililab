"""Test execute script"""

from unittest.mock import MagicMock, patch

import pytest
from qibo.gates import CNOT, RY, H, M, X
from qibo.models import Circuit

import qililab as ql
from qililab.pulse.pulse_schedule import PulseSchedule


def _prepare_qibo_circuit():
    n_qubits = 5
    result = Circuit(n_qubits)
    result.add([X(1), H(2), RY(0, 2), CNOT(4, 1), X(4), H(3), M(*range(5))])
    return result


circuit = _prepare_qibo_circuit()
pulse_schedule = PulseSchedule()


class TestExecute:
    """Test execute method in the `execute.py` script"""

    def test_execute(self):
        runcard = "galadriel.yml"
        mock_platform = MagicMock()
        mock_platform._translate_language.return_value = circuit
        with patch("qililab.execute_circuit.build_platform", return_value=mock_platform) as mock_build:
            results = ql.execute(circuit, runcard)
            assert isinstance(results, MagicMock)
            mock_build.assert_called_with(runcard="galadriel.yml")
        self._assert_calls_of_connect_setup_turnon_and_disconnect(mock_platform)
        mock_platform._translate_language.assert_called_once_with(program=circuit)
        mock_platform.execute.assert_called_once()

    def test_execute_calls_disconnect_after_error(self):
        runcard = "galadriel.yml"
        with pytest.raises(Exception):
            mock_platform = MagicMock()
            mock_platform.turn_on_instruments.side_effect = Exception()
            with patch("qililab.execute_circuit.build_platform", return_value=mock_platform) as mock_build:
                ql.execute(circuit, runcard)
            mock_build.assert_called_with(runcard="galadriel.yml")
            self._assert_calls_of_connect_setup_turnon_and_disconnect(mock_platform)
            mock_platform.execute.assert_not_called()

    @pytest.mark.parametrize(
        "circuits",
        [[circuit, circuit], (circuit, circuit), [pulse_schedule, pulse_schedule], [circuit, pulse_schedule]],
    )
    def test_execute_circuit_with_multiple_qibo_circuits(self, circuits):
        """Test that executing a list of circuits returns a list of results."""
        runcard = "galadriel.yml"
        mock_platform = MagicMock()
        with patch("qililab.execute_circuit.build_platform", return_value=mock_platform) as mock_build:
            results = ql.execute(circuits, runcard)
            assert isinstance(results, list)
            mock_build.assert_called_with(runcard="galadriel.yml")
        self._assert_calls_of_connect_setup_turnon_and_disconnect(mock_platform)
        assert mock_platform._translate_language.call_count == 2
        assert mock_platform.execute.call_count == 2

    @pytest.mark.parametrize(
        "circuits",
        [[circuit, circuit, "aads"], (circuit, circuit, "ads")],
    )
    def test_execute_circuit_with_error_in_multiple_circuits_(self, circuits):
        """Test that executing a list of circuits returns a list of results."""
        runcard = "galadriel.yml"
        mock_platform = MagicMock()
        with patch("qililab.execute_circuit.build_platform", return_value=mock_platform) as mock_build:
            results = ql.execute(circuits, runcard)
            assert isinstance(results, list)
            mock_build.assert_called_with(runcard="galadriel.yml")
        self._assert_calls_of_connect_setup_turnon_and_disconnect(mock_platform)
        assert mock_platform._translate_language.call_count == 3
        assert mock_platform.execute.call_count == 3
        assert mock_platform.disconnect.call_count == 1  # Disconnect is called after error

    def _assert_calls_of_connect_setup_turnon_and_disconnect(self, mock_platform):
        mock_platform.connect.assert_called_once_with()
        mock_platform.initial_setup.assert_called_once_with()
        mock_platform.turn_on_instruments.assert_called_once_with()
        mock_platform.disconnect.assert_called_once_with()
