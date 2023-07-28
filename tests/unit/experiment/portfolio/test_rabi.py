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
            platform = build_platform(name="flux_qubit")
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
        popt, idx = rabi.fit(p0=(8, 7.5 / (2 * np.pi), -np.pi / 2, 0))  # p0 is an initial guess

        assert idx == 0
        assert np.allclose(popt, (5.16800491e-11, 1.19387485e+00, -1.57050903e+00, 5.91287939e+00), atol=1e-5)

    def test_plot(self, rabi: Rabi):
        """Test plot method."""
        rabi.post_processed_results = [i, q]
        popt = rabi.fit()
        fig = rabi.plot()
        axes = fig.axes

        assert len(axes) == 2
        assert axes[0].get_xlabel() == 'Amplitude'
        assert axes[0].get_ylabel() == 'Voltage [a.u.]'
        assert axes[1].get_xlabel() == 'Amplitude'
        assert axes[1].get_ylabel() == 'Voltage [a.u.]'

        assert len(axes[0].lines)==2
        assert len(axes[1].lines)==1
        assert np.allclose(axes[0].lines[0].get_xdata(), rabi.loop.values)
        assert np.allclose(axes[0].lines[0].get_ydata(), i)
        assert np.allclose(axes[1].lines[0].get_xdata(), rabi.loop.values)
        assert np.allclose(axes[1].lines[0].get_ydata(), q)
