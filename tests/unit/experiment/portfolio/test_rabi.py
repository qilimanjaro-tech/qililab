"""Unit tests for the ``Rabi`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M, X

from qililab import build_platform
from qililab.experiment import Rabi
from qililab.system_control import ReadoutSystemControl
from qililab.typings import LoopOptions, Parameter
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
    analysis = Rabi(platform=platform, qubit=0, loop_options=LoopOptions(start=START, stop=STOP, num=NUM))
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
        assert rabi.options.loops[0].alias == "X"
        assert rabi.options.loops[0].parameter == "amplitude"
        assert rabi.options.loops[0].options.start == START
        assert rabi.options.loops[0].options.stop == STOP
        assert rabi.options.loops[0].options.num == NUM
        assert rabi.options.settings.repetition_duration == 10000
        assert rabi.options.settings.hardware_average == 10000
        assert rabi.options.plot_y_label == "|S21| [dB]"

    def test_bus_setup_with_control_true(self, rabi: Rabi):
        """Test the ``bus_setup`` method with ``control=True``."""
        rabi.control_bus = MagicMock()
        rabi.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=True)
        rabi.control_bus.set_parameter.assert_called_once_with(parameter=Parameter.AMPLITUDE, value=0.6)

    def test_bus_setup_with_control_false(self, rabi: Rabi):
        """Test the ``bus_setup`` method with ``control=False``."""
        rabi.readout_bus = MagicMock()
        rabi.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=False)
        rabi.readout_bus.set_parameter.assert_called_once_with(parameter=Parameter.AMPLITUDE, value=0.6)

    def test_control_gate_setup(self, rabi: Rabi):
        """Test the ``control_gate_setup`` method."""
        assert not hasattr(rabi, "execution")  # ``build_execution`` has not been called
        rabi.control_gate_setup(parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(rabi, "execution")  # ``build_execution`` has been called
        assert rabi.platform.get_element("X").amplitude == 123

    def test_measurement_setup(self, rabi: Rabi):
        """Test the ``measurement_setup`` method."""
        assert not hasattr(rabi, "execution")  # ``build_execution`` has not been called
        rabi.measurement_setup(parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(rabi, "execution")  # ``build_execution`` has been called
        assert rabi.platform.get_element("M").amplitude == 123

    def test_func(self, rabi: Rabi):
        """Test the ``func`` method."""
        assert np.allclose(rabi.func(xdata=x, a=5, b=7), i)

    def test_fit(self, rabi: Rabi):
        """Test fit method."""
        rabi.post_processed_results = q
        popt = rabi.fit(p0=(8, 7.5))  # p0 is an initial guess
        assert all(popt == (9, 7))

    def test_plot(self, rabi: Rabi):
        """Test plot method."""
        rabi.post_processed_results = q
        popt = rabi.fit()
        fig = rabi.plot()
        ax = fig.axes[0]
        assert len(ax.lines) == 2
        line0 = ax.lines[0]
        assert np.allclose(line0.get_xdata(), x)
        assert np.allclose(line0.get_ydata(), q)
        line1 = ax.lines[1]
        assert np.allclose(line1.get_xdata(), x)
        assert np.allclose(line1.get_ydata(), popt[0] * np.sin(popt[1] * x))
