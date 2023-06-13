import re
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
from qibo.backends import NumpyBackend
from qibo.gates import RX, RZ, M, X
from qibo.models import Circuit

from qililab import build_platform
from qililab.experiment import xBellStates
from qililab.system_control import ReadoutSystemControl
from tests.data import Galadriel

bell_state_names = ["phi_plus", "phi_minus", "psi_plus", "psi_minus"]


START = 1
STOP = 5
NUM = 2
x = np.linspace(START, STOP, NUM)
i = 5 * np.sin(7 * x)
q = 9 * np.sin(7 * x)


@pytest.fixture(name="xbell")
def xbell():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
            xBell = xBellStates(
                control_qubit=0,
                target_qubit=1,
                platform=platform,
                theta_loop_values=np.linspace(0, np.pi, NUM),
                bell_state="phi_plus",
                repetition_duration=200_000,
                hardware_average=1,
                num_bins=2_000,
            )

            xBell.results = MockResult()
            return xBell


@pytest.fixture(name="xbell_pure")
def xbell_pure(request):
    """Return Experiment object. For pure states. Parametrized fixture"""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard):
        with patch("qililab.platform.platform_manager_yaml.open"):
            platform = build_platform(name="flux_qubit")
            return xBellStates(
                control_qubit=0,
                target_qubit=1,
                platform=platform,
                theta_loop_values=[],
                bell_state=request.param,
                repetition_duration=200_000,
                hardware_average=1,
                num_bins=2_000,
            )


@pytest.fixture(name="bell_states")
def fixture_bell_states():
    """Returns bell states"""
    # FIXME: gate decomposition from the template for CHSH is probably wrong
    # contrast this with Ramiro (he wrote the experiment's circuit)
    return {
        "phi_plus": np.array([np.sqrt(2) / 2, 0, 0, -1 * np.sqrt(2) / 2]),
        "phi_minus": np.array([np.sqrt(2) / 2, 0, 0, np.sqrt(2) / 2]),
        "psi_plus": np.array([0, np.sqrt(2) / 2, np.sqrt(2) / 2, 0]),
        "psi_minus": np.array([0, np.sqrt(2) / 2, -1 * np.sqrt(2) / 2, 0]),
    }


# mocks for acquisitions = result.resultss[idx]
class MockResult(Mock):
    def __getitem__(self, key):
        return MockProbability(key)  # it's probabilities so should be 0 < return < 1


class MockProbability:
    def __init__(self, key):
        self.key = key

    def probabilities(self):
        psi_plus = [0.5]
        psi_minus = [0.2]
        phi_plus = [1]
        phi_minus = [0.8]
        return pd.DataFrame(zip(psi_plus, psi_minus, phi_plus, phi_minus), columns=["00", "01", "10", "11"])


def apply_circuit(circuit: Circuit) -> np.ndarray:
    """Copied from unit tests for the native gate transpiler
    Apples native gates from a transpiled circuit as qibo
    Drag pulses are translated to supported qibo.gates RX, RZ.
    Gates are applied onto initial state |00...0>
    Backend is set to numpy for faster execution since circuits are small

    Args:
        circuit (Circuit): transpiled qibo circuit to be executed

    Returns:
        state (np.ndarray): resulting state
    """

    backend = NumpyBackend()

    nqubits = circuit.nqubits
    # start initial state |00...0>
    state = np.zeros(2**nqubits)
    state[0] = 1
    for gate in circuit.queue:
        if gate.name == "rz":
            state = backend.apply_gate(gate, state, nqubits)
        if gate.name == "drag":
            theta = gate.parameters[0]
            phi = gate.parameters[1]
            qubit = gate.qubits[0]
            # apply Drag gate as RZ and RX gates
            state = backend.apply_gate(RZ(qubit, -phi), state, nqubits)
            state = backend.apply_gate(RX(qubit, theta), state, nqubits)
            state = backend.apply_gate(RZ(qubit, phi), state, nqubits)

        if gate.name == "cz":
            state = backend.apply_gate(gate, state, nqubits)

    return state


class TestxBellStates:
    def test_init(self, xbell):
        assert xbell.control_qubit == 0
        assert xbell.target_qubit == 1
        assert np.allclose(xbell.theta_loop_values, np.linspace(0, np.pi, NUM))
        assert xbell.bell_state == "phi_plus"
        assert xbell.nqubits == 1
        circuit = xbell._get_chsh_circuit() + xbell._get_decoder_circuits()
        assert [(gate.name, gate.qubits) for gate in circuit.queue] == [
            ("drag", (0,)),
            ("drag", (1,)),
            ("cz", (0, 1)),
            ("drag", (1,)),
            ("drag", (0,)),
            ("drag", (0,)),
            ("drag", (1,)),
            ("measure", (0,)),
            ("measure", (1,)),
        ]

    @pytest.mark.parametrize("xbell_pure", bell_state_names, indirect=True)
    def test_bell_states(self, xbell_pure, bell_states):
        """Check that bell state circuits create the expected circuit"""
        c = xbell_pure._get_chsh_circuit()
        assert np.allclose(apply_circuit(c), bell_states[xbell_pure.bell_state])

    @patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard)
    @patch("qililab.platform.platform_manager_yaml.open")
    def test_wrong_state_error(self, mock_load, mock_open, xbell: xBellStates):
        platform = build_platform(name="flux_qubit")

        error_string = re.escape(f"bell_state needs to be in {bell_state_names}")
        with pytest.raises(ValueError, match=error_string):
            xBellStates(
                control_qubit=2,
                target_qubit=1,
                platform=platform,
                theta_loop_values=np.linspace(0, np.pi, NUM),
                bell_state="no_state",
                repetition_duration=200_000,
                hardware_average=1,
                num_bins=2_000,
            )

    def test_post_process_results(self, xbell):
        results = xbell.post_process_results()

        assert np.allclose(results, np.array([[[0.1, 0.1], [0.1, 0.1]], [[0.1, 0.1], [0.1, 0.1]]]))

    def test_get_chsh_witness(self, xbell):
        xbell.post_process_results()
        assert np.allclose(xbell.get_chsh_witness(), np.array([[0.2, 0.2], [0.2, 0.2]]))
