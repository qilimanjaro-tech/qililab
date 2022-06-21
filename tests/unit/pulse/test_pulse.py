"""Tests for the Pulse class."""
import numpy as np
import pytest

from qililab.pulse import Pulse
from qililab.utils import Waveforms


class TestPulse:
    """Unit tests checking the Pulse attributes and methods"""

    def test_modulated_waveforms_method(self, pulse: Pulse):
        """Test modulated_waveforms method."""
        waveforms = pulse.modulated_waveforms(frequency=1e9)
        assert isinstance(waveforms, Waveforms)

    def test_start_property_raises_error(self, pulse: Pulse):
        """Test that start property raises error when star_time is None"""
        pulse.start_time = None
        with pytest.raises(ValueError):
            pulse.start  # pylint: disable=pointless-statement

    def test_envelope_method(self, pulse: Pulse):
        """Test envelope method"""
        envelope = pulse.envelope(amplitude=2.0, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()
        assert isinstance(dictionary, dict)

    def test_instantiate_pulse_with_dict(self, pulse: Pulse):
        """Test instantiation of pulse with a dictionary."""
        pulse_shape = pulse.pulse_shape.to_dict()
        pulse = Pulse(amplitude=1.0, phase=0, duration=10, qubit_ids=[3], pulse_shape=pulse_shape)
        assert pulse.pulse_shape.to_dict() == {"name": "gaussian"} | pulse_shape
