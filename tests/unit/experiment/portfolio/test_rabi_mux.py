"""Unit tests for the ``Rabi`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M, X

from qililab import build_platform
from qililab.experiment import RabiMux
from qililab.system_control import ReadoutSystemControl
from tests.data import Galadriel

# Theta loop parameters
THETA_START = 0
THETA_END = 2 * np.pi
THETA_NUM_SAMPLES = 51

theta_values = np.linspace(THETA_START, THETA_END, THETA_NUM_SAMPLES)

# Modulaiton parameters
i = 5 * np.sin(7 * theta_values)
q = 9 * np.sin(7 * theta_values)


@pytest.fixture(name="rabi_mux")
def fixture_rabi_mux() -> RabiMux:
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = RabiMux(platform=platform, qubit_theta=0, qubit_2theta=1, theta_values=theta_values)
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestRabi:
    """Unit tests for the ``Rabi`` class."""

    def test_init(self, rabi_mux: RabiMux):
        """Test the ``__init__`` method."""
        # Test that the correct circuit is created
        assert len(rabi_mux.circuits) == 1
        for gate in rabi_mux.circuits[0].queue:
            assert isinstance(gate, (X, M))
            assert gate.qubits == (0,)
        # Test the bus attributes
        assert not isinstance(rabi_mux.control_bus.system_control, ReadoutSystemControl)
        assert isinstance(rabi_mux.readout_bus.system_control, ReadoutSystemControl)
        # Test the experiment options
        assert len(rabi_mux.options.loops) == 1
        assert rabi_mux.loop.alias == "X"
        assert rabi_mux.loop.parameter == "amplitude"
        assert rabi_mux.loop.start == THETA_START
        assert rabi_mux.loop.stop == THETA_END
        assert rabi_mux.loop.num == THETA_NUM_SAMPLES
        assert rabi_mux.options.settings.repetition_duration == 10000
        assert rabi_mux.options.settings.hardware_average == 10000

    def test_func(self, rabi_mux: RabiMux):
        """Test the ``func`` method."""
        assert np.allclose(
            rabi_mux.func(xdata=theta_values, amplitude=5, frequency=7 / (2 * np.pi), phase=-np.pi / 2, offset=0),
            i,
        )

    def test_fit(self, rabi_mux: RabiMux):
        """Test fit method."""
        rabi_mux.post_processed_results = q
        popt = rabi_mux.fit(p0=(8, 7.5 / (2 * np.pi), -np.pi / 2, 0))  # p0 is an initial guess
        assert np.allclose(popt, (9, 7 / (2 * np.pi), -np.pi / 2, 0), atol=1e-5)

    def test_plot(self, rabi_mux: RabiMux):
        """Test plot method."""
        rabi_mux.post_processed_results = q
        popt = rabi_mux.fit()
        fig = rabi_mux.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], theta_values)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), theta_values)
        assert np.allclose(line.get_ydata(), popt[0] * np.cos(2 * np.pi * popt[1] * theta_values + popt[2]) + popt[3])
