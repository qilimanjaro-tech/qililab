"""Unit tests for the ``Rabi`` class."""
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import numpy as np
import pytest

from qililab import build_platform
from qililab.experiment import ResonatorSpectroscopy
from tests.data import Galadriel

FREQUENCY_START = 8.1e9
FREQUENCY_STOP = 8.13e9
FREQUENCY_NUM = 101

START = 1
STOP = 5
NUM = 1000
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


@pytest.fixture(name="resonator_spectroscopy0")
def fixture_resonator_spectroscopy0(platform):
    """Return experiment object."""
    frequency_array = np.linspace(FREQUENCY_START, FREQUENCY_STOP, FREQUENCY_NUM)

    experiment = ResonatorSpectroscopy(
        qubit=0,
        platform=platform,
        freq_values=frequency_array,
        gain_values=None,
        attenuation_values=None,
        sweep_if=False,
        repetition_duration=10000,
        hardware_average=10000,
    )

    experiment.results = MagicMock()
    experiment.results.acquisitions.return_value = {
        "i": 5 * np.sin(7 * frequency_array),
        "q": 9 * np.sin(7 * frequency_array),
    }
    experiment.results_path = MagicMock()
    return experiment


@pytest.fixture(name="resonator_spectroscopy_gain")
def fixture_resonator_spectroscopy_gain(platform):
    """Return platform object."""
    frequency_array = np.linspace(FREQUENCY_START, FREQUENCY_STOP, FREQUENCY_NUM)
    gain_values = np.linspace(start=START, stop=STOP, num=NUM)
    experiment = ResonatorSpectroscopy(
        qubit=0,
        platform=platform,
        freq_values=frequency_array,
        gain_values=gain_values,
        attenuation_values=None,
        sweep_if=False,
        repetition_duration=10000,
        hardware_average=10000,
    )

    experiment.results = MagicMock()
    experiment.results.acquisitions.return_value = {
        "i": np.tile(i, FREQUENCY_NUM),
        "q": np.tile(q, FREQUENCY_NUM),
    }
    return experiment


@pytest.fixture(name="resonator_spectroscopy_atten")
def fixture_resonator_spectroscopy_atten(platform):
    """Return platform object."""
    frequency_array = np.linspace(FREQUENCY_START, FREQUENCY_STOP, FREQUENCY_NUM)
    attenuation_values = np.linspace(start=START, stop=STOP, num=NUM)
    experiment = ResonatorSpectroscopy(
        qubit=0,
        platform=platform,
        freq_values=frequency_array,
        gain_values=None,
        attenuation_values=attenuation_values,
        sweep_if=False,
        repetition_duration=10000,
        hardware_average=10000,
    )

    experiment.results = MagicMock()
    experiment.results.acquisitions.return_value = {
        "i": np.tile(i, FREQUENCY_NUM),
        "q": np.tile(q, FREQUENCY_NUM),
    }
    return experiment


class TestResonatorSpectroscopy:
    """Unit tests for the ``ResonatorSpectroscopy`` class."""

    def test_init(self, resonator_spectroscopy0: ResonatorSpectroscopy):
        """Test the ``__init__`` method."""
        assert resonator_spectroscopy0.loop.start == FREQUENCY_START
        assert resonator_spectroscopy0.loop.stop == FREQUENCY_STOP
        assert resonator_spectroscopy0.loop.num == FREQUENCY_NUM
        assert resonator_spectroscopy0.loop.alias == "feedline_bus"
        assert resonator_spectroscopy0.options.settings.repetition_duration == 10000
        assert resonator_spectroscopy0.options.settings.hardware_average == 10000

    def test_plot(self, resonator_spectroscopy0: ResonatorSpectroscopy):
        """Test the ``plot`` method."""
        resonator_spectroscopy0.post_process_results()
        plt.clf()
        fig = resonator_spectroscopy0.plot()
        line = fig.gca().lines[0]
        x_data = line.get_xdata()

        assert np.allclose(x_data, resonator_spectroscopy0.freq_values)

    def test_post_process_results_gain(self, resonator_spectroscopy_gain: ResonatorSpectroscopy):
        """Test the ``post_process_results`` method of an experiment with gain"""
        resonator_spectroscopy_gain.post_process_results()
        expected = 20 * np.log10(np.sqrt(i[:FREQUENCY_NUM] ** 2 + q[:FREQUENCY_NUM] ** 2))

        assert np.shape(resonator_spectroscopy_gain.post_processed_results) == (NUM, FREQUENCY_NUM)
        assert np.allclose(resonator_spectroscopy_gain.post_processed_results[0], expected)

        plt.clf()
        fig = resonator_spectroscopy_gain.plot()
        ax = fig.gca()
        collection = ax.collections[0]
        masked_data = collection.get_array()

        data = np.ma.getdata(masked_data)

        assert np.allclose(data, resonator_spectroscopy_gain.post_processed_results.flatten())

    def test_post_process_results_aten(self, resonator_spectroscopy_atten: ResonatorSpectroscopy):
        """Test the ``post_process_results`` method of an experiment with atenuation"""
        resonator_spectroscopy_atten.post_process_results()
        expected = 20 * np.log10(np.sqrt(i[:FREQUENCY_NUM] ** 2 + q[:FREQUENCY_NUM] ** 2))

        assert np.shape(resonator_spectroscopy_atten.post_processed_results) == (NUM, FREQUENCY_NUM)
        assert np.allclose(resonator_spectroscopy_atten.post_processed_results[0], expected)

        plt.clf()
        fig = resonator_spectroscopy_atten.plot()
        ax = fig.gca()
        collection = ax.collections[0]
        masked_data = collection.get_array()

        data = np.ma.getdata(masked_data)

        assert np.allclose(data, resonator_spectroscopy_atten.post_processed_results.flatten())
