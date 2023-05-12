"""Tests for the Pulse class."""
import numpy as np
import pytest

from qililab.pulse import Gaussian, Pulse, PulseEvent
from qililab.utils import Waveforms


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


class TestPulseEvent:
    """Unit tests checking the PulseEvent attributes and methods"""

    def test_modulated_waveforms_method(self, pulse_event: PulseEvent):
        """Test modulated_waveforms method."""
        waveforms = pulse_event.modulated_waveforms()
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse_event: PulseEvent):
        """Test envelope method"""
        envelope = pulse_event.pulse.envelope(amplitude=2.0, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse_event: PulseEvent):
        """Test to_dict method"""
        dictionary = pulse_event.to_dict()
        assert isinstance(dictionary, dict)

    def test_end_time(self, pulse_event: PulseEvent):
        """Test end_time property."""
        assert pulse_event.duration == pulse_event.end_time - pulse_event.start_time
