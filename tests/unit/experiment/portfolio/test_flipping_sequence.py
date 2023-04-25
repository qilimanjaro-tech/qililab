"""Unit tests for the ``FlippingSequence`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import RX, M, X

from qililab import build_platform
from qililab.experiment import FlippingSequence
from qililab.system_control import ReadoutSystemControl
from tests.data import Galadriel

START = 1
STOP = 1000
STEP = 2
x = np.arange(START, STOP, step=STEP)
i = 5 * np.sin(0.01 * x)
q = 9 * np.sin(0.01 * x)


@pytest.fixture(name="flipping_sequence")
def fixture_flipping_sequence():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = FlippingSequence(platform=platform, qubit=0, loop_values=np.arange(start=START, stop=STOP, step=STEP))
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestFlippingSequence:
    """Unit tests for the ``FlippingSequence`` class."""

    def test_init(self, flipping_sequence: FlippingSequence):
        """Test the ``__init__`` method."""
        # Test that the correct circuit is created
        assert len(flipping_sequence.circuits) == STOP // STEP - START // STEP
        for i, circuit in enumerate(flipping_sequence.circuits):
            assert len(circuit.queue) == 2 + 2 * (START + STEP * i)
            for gate in circuit.queue:
                if isinstance(gate, RX):
                    assert np.allclose(gate.parameters, np.pi / 2)
                else:
                    assert isinstance(gate, (X, M))
                assert gate.qubits == (0,)
        # Test the bus attributes
        assert not isinstance(flipping_sequence.control_bus.system_control, ReadoutSystemControl)
        assert isinstance(flipping_sequence.readout_bus.system_control, ReadoutSystemControl)
        # Test the experiment options
        assert flipping_sequence.options.loops is None
        assert flipping_sequence.options.settings.repetition_duration == 10000
        assert flipping_sequence.options.settings.hardware_average == 10000
        assert flipping_sequence.options.plot_y_label == "|S21| [dB]"

    def test_func(self, flipping_sequence: FlippingSequence):
        """Test the ``func`` method."""
        assert np.allclose(
            flipping_sequence.func(xdata=x, amplitude=5, frequency=0.01 / (2 * np.pi), phase=-np.pi / 2, offset=0),
            i,
        )

    def test_fit(self, flipping_sequence: FlippingSequence):
        """Test fit method."""
        flipping_sequence.post_processed_results = q
        popt = flipping_sequence.fit(p0=(-8, 0.005 / (2 * np.pi), 3 * np.pi / 2, 0))  # p0 is an initial guess
        assert np.allclose(popt, (-9, 0.01 / (2 * np.pi), np.pi / 2, 0), atol=1e-5)

    def test_plot(self, flipping_sequence: FlippingSequence):
        """Test plot method."""
        flipping_sequence.post_processed_results = q
        popt = flipping_sequence.fit()
        fig = flipping_sequence.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], x)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), x)
        assert np.allclose(line.get_ydata(), popt[0] * np.cos(2 * np.pi * popt[1] * x + popt[2]) + popt[3])
