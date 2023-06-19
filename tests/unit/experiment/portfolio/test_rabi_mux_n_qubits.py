"""Unit tests for the ``RabiMuxNQubits`` portfolio experiment class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from matplotlib.figure import Figure
from qibo.gates import M

from qililab import build_platform
from qililab.experiment import RabiMuxNQubits
from qililab.transpiler import Drag
from qililab.typings import Parameter
from qililab.utils import Wait
from tests.data import Galadriel

# Qubits parameters
QUBIT_LIST = [0, 1]

# Theta loop parameters
THETA_START = 0
THETA_END = 2 * np.pi
THETA_NUM_SAMPLES = 51
theta_values = np.linspace(THETA_START, THETA_END, THETA_NUM_SAMPLES)

# Modulaiton parameters
I_AMPLITUDE, I_FREQ, I_PHASE, I_OFFSET = (5, 7, 0, 0)
Q_AMPLITUDE, Q_FREQ, Q_PHASE, Q_OFFSET = (9, 7, 0, 0)
i = I_AMPLITUDE * np.cos(2 * np.pi * I_FREQ * theta_values + I_PHASE) + I_OFFSET
q = Q_AMPLITUDE * np.cos(2 * np.pi * Q_FREQ * theta_values + Q_PHASE) + Q_OFFSET


@pytest.fixture(name="rabi_mux_n_qubits")
def fixture_rabi_mux_n_qubits() -> RabiMuxNQubits:
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="_")
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

        for index, _ in enumerate(QUBIT_LIST):
            assert rabi_mux_n_qubits.options.loops[index].alias == str(3 * index)
            assert rabi_mux_n_qubits.options.loops[index].parameter == Parameter.GATE_PARAMETER
            assert rabi_mux_n_qubits.options.loops[index].start == THETA_START
            assert rabi_mux_n_qubits.options.loops[index].stop == THETA_END * (index + 1)
            assert rabi_mux_n_qubits.options.loops[index].num == THETA_NUM_SAMPLES

        assert rabi_mux_n_qubits.options.settings.repetition_duration == 1000
        assert rabi_mux_n_qubits.options.settings.hardware_average == 1000
        assert rabi_mux_n_qubits.options.settings.num_bins == 1

    def test_func(self, rabi_mux_n_qubits: RabiMuxNQubits):
        """Test the ``func`` method."""
        assert np.allclose(
            rabi_mux_n_qubits.func(
                xdata=theta_values, amplitude=I_AMPLITUDE, frequency=I_FREQ, phase=I_PHASE, offset=I_OFFSET
            ),
            i,
        )

    @patch("qililab.experiment.portfolio.ExperimentAnalysis.post_process_results")
    def test_post_process_results(
        self, mock_parent_post_process_results: np.ndarray, rabi_mux_n_qubits: RabiMuxNQubits
    ):
        """Test the post_process_results method."""
        rabi_mux_n_qubits.post_processed_results = np.concatenate([q, q])
        res = rabi_mux_n_qubits.post_process_results()

        assert res.shape == (THETA_NUM_SAMPLES, len(QUBIT_LIST))
        assert np.allclose(
            rabi_mux_n_qubits.options.loops[0].values, np.linspace(THETA_START, THETA_END, THETA_NUM_SAMPLES)
        )

    def test_plot_returns_figure(self, rabi_mux_n_qubits: RabiMuxNQubits):
        """Test plot method."""
        rabi_mux_n_qubits.post_processed_results = np.concatenate([q, q]).reshape(THETA_NUM_SAMPLES, 2)
        fig = rabi_mux_n_qubits.plot()
        ax = fig.axes[0]
        line_0, line_1 = ax.lines[0], ax.lines[1]

        assert np.allclose(line_0.get_xdata(), theta_values)
        assert np.allclose(line_0.get_ydata(), rabi_mux_n_qubits.post_processed_results[:, 0])
        assert np.allclose(line_1.get_ydata(), rabi_mux_n_qubits.post_processed_results[:, 1])
        assert isinstance(fig, Figure)

    @patch("qililab.experiment.portfolio.rabi_mux_n_qubits.plt")
    def test_plot_steps(self, mock_plt, rabi_mux_n_qubits: RabiMuxNQubits):
        """Test plot method steps."""
        rabi_mux_n_qubits.post_processed_results = np.concatenate([q, q]).reshape(THETA_NUM_SAMPLES, 2)
        _ = rabi_mux_n_qubits.plot()

        mock_plt.figure.assert_called_once_with()
        mock_plt.plot.assert_called()
        mock_plt.title.assert_called_once_with(rabi_mux_n_qubits.options.name)
        mock_plt.xlabel.assert_called_once_with(
            f"{rabi_mux_n_qubits.loop.alias}:{rabi_mux_n_qubits.loop.parameter.value}"
        )
        mock_plt.ylabel.assert_called_once_with("|S21| [dB]")
        mock_plt.legend.assert_called_once_with(loc="upper right")
