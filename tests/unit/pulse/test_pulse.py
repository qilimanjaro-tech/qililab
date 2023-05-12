"""Tests for the Pulse class."""
import numpy as np
import pytest

from qililab.pulse import Gaussian, Pulse
from qililab.utils import Waveforms


@pytest.fixture(name="pulse")
def fixture_pulse() -> Pulse:
    """Load Pulse.

    Returns:
        Pulse: Instance of the Pulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)


class TestPulse:
    """Unit tests checking the Pulse attributes and methods"""

    def test_modulated_waveforms_method(self, pulse: Pulse):
        """Test modulated_waveforms method."""
        waveforms = pulse.modulated_waveforms()
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse: Pulse):
        """Test envelope method"""
        envelope = pulse.envelope(amplitude=2.0, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()
        assert isinstance(dictionary, dict)
