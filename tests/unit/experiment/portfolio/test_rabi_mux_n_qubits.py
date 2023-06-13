"""Unit tests for the ``RabiMuxNQubits`` portfolio experiment class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M

from qililab import build_platform
from qililab.experiment import RabiMuxNQubits
from qililab.system_control import ReadoutSystemControl
from qililab.transpiler import Drag
from qililab.typings import Parameter
from qililab.typings.enums import Qubits
from qililab.utils import Wait
from tests.data import Galadriel

# Qubits parameters
QUBIT_LIST = [0, 2]

# Theta loop parameters
THETA_START = 0
THETA_END = 2 * np.pi
THETA_NUM_SAMPLES = 51
theta_values = np.linspace(THETA_START, THETA_END, THETA_NUM_SAMPLES)

# Modulaiton parameters
I_AMPLITUDE, I_RATE = (5, 7)
Q_AMPLITUDE, Q_RATE = (9, 7)
i = I_AMPLITUDE * np.exp(I_RATE * theta_values)
q = Q_AMPLITUDE * np.exp(Q_RATE * theta_values)


@pytest.fixture(name="rabi_mux_n_qubits")
def fixture_rabi_mux_nqubits() -> RabiMuxNQubits:
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = RabiMuxNQubits(platform=platform, qubits=QUBIT_LIST, theta_values=theta_values)
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestRabi:
    """Unit tests for the ``RabiMux`` portfolio experiment class."""

    def test_init(self, rabi_mux_n_qubits: RabiMuxNQubits):
        """Test the ``__init__`` method."""
        # Test that the correct circuit is created
        assert len(rabi_mux_n_qubits.circuits) == 1
        for idx, gate in enumerate(rabi_mux_n_qubits.circuits[0].queue):
            assert isinstance(gate, [Drag, Wait, M][idx % 3])
            assert gate.qubits == (QUBIT_LIST[idx // 3],)

        # Test the experiment options
        assert len(rabi_mux_n_qubits.options.loops) == 2

        for id, _ in enumerate(QUBIT_LIST):
            assert rabi_mux_n_qubits.options.loops[id].alias == str(3 * id)
            assert rabi_mux_n_qubits.options.loops[id].parameter == Parameter.GATE_PARAMETER
            assert rabi_mux_n_qubits.options.loops[id].start == THETA_START
            assert rabi_mux_n_qubits.options.loops[id].stop == THETA_END * (id + 1)
            assert rabi_mux_n_qubits.options.loops[id].num == THETA_NUM_SAMPLES

        assert rabi_mux_n_qubits.options.settings.repetition_duration == 1000
        assert rabi_mux_n_qubits.options.settings.hardware_average == 1000
        assert rabi_mux_n_qubits.options.settings.num_bins == 1

    # TO DO: Here down vvv is incorrect!!!!!!!!!!
    # (maybe you even need to change the fixture, or add a new ficture for post_process)

    def test_post_process_results(self, rabi_mux_n_qubits: RabiMuxNQubits):
        """Test the post_process_results method."""
        assert rabi_mux_n_qubits.post_process_results().shape() == (len(rabi_mux_n_qubits.theta_values), 2)

    def test_plot(self, rabi_mux_n_qubits: RabiMuxNQubits):
        """Test plot method."""
        rabi_mux_n_qubits.post_processed_results = q
        popt = rabi_mux_n_qubits.fit()
        fig = rabi_mux_n_qubits.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], theta_values)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), theta_values)
        assert np.allclose(line.get_ydata(), popt[0] * np.cos(2 * np.pi * popt[1] * theta_values + popt[2]) + popt[3])
