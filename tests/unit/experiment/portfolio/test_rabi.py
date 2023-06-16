"""Unit tests for the ``Rabi`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M, X

from qililab import build_platform
from qililab.experiment import Rabi
from qililab.system_control import ReadoutSystemControl
from tests.data import Galadriel

START = 1
STOP = 5
NUM = 1000
x = np.linspace(START, STOP, NUM)
i = 5 * np.sin(7 * x)
q = 9 * np.sin(7 * x)


@pytest.fixture(name="rabi")
def fixture_rabi():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="_")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = Rabi(platform=platform, qubit=0, loop_values=np.linspace(start=START, stop=STOP, num=NUM))
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestRabi:
    """Unit tests for the ``Rabi`` class."""

    def test_init(self, rabi: Rabi):
        """Test the ``__init__`` method."""
        # Test that the correct circuit is created
        assert len(rabi.circuits) == 1
        for gate in rabi.circuits[0].queue:
            assert isinstance(gate, (X, M))
            assert gate.qubits == (0,)
        # Test the bus attributes
        assert not isinstance(rabi.control_bus.system_control, ReadoutSystemControl)
        assert isinstance(rabi.readout_bus.system_control, ReadoutSystemControl)
        # Test the experiment options
        assert len(rabi.options.loops) == 1
        assert rabi.loop.alias == "X"
        assert rabi.loop.parameter == "amplitude"
        assert rabi.loop.start == START
        assert rabi.loop.stop == STOP
        assert rabi.loop.num == NUM
        assert rabi.options.settings.repetition_duration == 10000
        assert rabi.options.settings.hardware_average == 10000

    def test_func(self, rabi: Rabi):
        """Test the ``func`` method."""
        assert np.allclose(
            rabi.func(xdata=x, amplitude=5, frequency=7 / (2 * np.pi), phase=-np.pi / 2, offset=0),
            i,
        )

    def test_fit(self, rabi: Rabi):
        """Test fit method."""
        rabi.post_processed_results = q
        popt = rabi.fit(p0=(8, 7.5 / (2 * np.pi), -np.pi / 2, 0))  # p0 is an initial guess
        assert np.allclose(popt, (9, 7 / (2 * np.pi), -np.pi / 2, 0), atol=1e-5)

    def test_plot(self, rabi: Rabi):
        """Test plot method."""
        rabi.post_processed_results = q
        popt = rabi.fit()
        fig = rabi.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], x)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), x)
        assert np.allclose(line.get_ydata(), popt[0] * np.cos(2 * np.pi * popt[1] * x + popt[2]) + popt[3])
