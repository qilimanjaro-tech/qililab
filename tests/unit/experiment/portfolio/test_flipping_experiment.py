"""Unit tests for the ``Rabi`` class."""
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import numpy as np
import pytest

from qililab import build_platform
from qililab.experiment import FlippingExperiment
from tests.data import Galadriel

START = 0.131
STOP = 0.151
NUM = 21
x = np.linspace(START, STOP, NUM)
i = 5 * np.sin(7 * x)
q = 9 * np.sin(7 * x)


@pytest.fixture(name="platform")
def fixture_platform():
    """Return platform object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()

    return platform


@pytest.fixture(name="flipping")
def fixture_flipping(platform):
    """Return experiment object."""
    flips_values = np.arange(0, 10, 1)
    amplitude_values = np.linspace(START, STOP, NUM)

    experiment = FlippingExperiment(
        platform=platform,
        qubit=0,
        flips_values=flips_values,
        amplitude_values=amplitude_values,
        repetition_duration=10000,
        measurement_buffer=100,
        hardware_average=10000,
    )

    x = np.linspace(START, STOP, NUM)
    i = 5 * np.sin(7 * x)
    q = 9 * np.sin(7 * x)

    experiment.results = MagicMock()
    experiment.results.acquisitions.return_value = {
        "i": np.tile(i, 10),
        "q": np.tile(q, 10),
    }
    experiment.results_path = MagicMock()
    return experiment


class TestFlippingExperiment:
    """Unit tests for the ``ResonatorSpectroscopy`` class."""

    def test_init(self, flipping: FlippingExperiment):
        """Test the ``__init__`` method."""
        assert flipping.loop.start == START
        assert flipping.loop.stop == STOP
        assert flipping.loop.num == NUM
        assert flipping.loop.alias == "Drag(0)"
        assert flipping.options.settings.repetition_duration == 10000
        assert flipping.options.settings.hardware_average == 10000

    def test_post_process_results(self, flipping: FlippingExperiment):
        """Test the ``post_process_results`` method."""
        flipping.post_process_results()
        expected = np.tile(20 * np.log10(np.sqrt(i**2 + q**2)), 10)

        assert np.shape(flipping.post_processed_results) == (NUM, 10)
        assert np.allclose(flipping.post_processed_results.flatten(), expected)

    def test_plot(self, flipping: FlippingExperiment):
        """Test the ``plot`` method."""
        flipping.post_process_results()

        plt.clf()
        fig = flipping.plot()
        ax = fig.gca()
        collection = ax.collections[0]
        masked_data = collection.get_array()

        data = np.ma.getdata(masked_data)

        assert np.allclose(data, flipping.post_processed_results.flatten())

    def test_plot_lines(self, flipping: FlippingExperiment):
        """Test the ``plot`` method."""
        flipping.post_process_results()

        plt.clf()
        fig = flipping.plot_lines()
        line = fig.gca().lines[0]
        x_data = line.get_xdata()

        assert np.allclose(x_data, flipping.flips_values)
