"""Tests for the Pulse class."""
import numpy as np
import pytest

from qililab.pulse import PulseEvent
from qililab.utils import Waveforms


class TestPulseEvent:
    """Unit tests checking the PulseEvent attributes and methods"""

    def test_modulated_waveforms_method(self, pulse_event: PulseEvent):
        """Test modulated_waveforms method."""
        waveforms = pulse_event.modulated_waveforms()
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse_event: PulseEvent):
        """Test envelope method"""
        envelope = pulse_event.pulses.envelope(amplitude=2.0, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse_event: PulseEvent):
        """Test to_dict method"""
        dictionary = pulse_event.to_dict()
        assert isinstance(dictionary, dict)
