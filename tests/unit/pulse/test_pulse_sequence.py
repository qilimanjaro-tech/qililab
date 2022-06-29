"""Tests for the PulseSequence class."""
import numpy as np
import pytest

from qililab.pulse import Pulse, PulseSequence


class TestPulseSequence:
    """Unit tests checking the PulseSequence attributes and methods"""

    def test_add_method(self, pulse_sequence: PulseSequence, pulse: Pulse):
        """Test add method."""
        pulse.port = pulse_sequence.port
        pulse_sequence.add(pulse=pulse)

    def test_add_method_with_wrong_port(self, pulse_sequence: PulseSequence, pulse: Pulse):
        """Test add method with wrong port"""
        pulse.port = 123
        with pytest.raises(ValueError):
            pulse_sequence.add(pulse=pulse)

    def test_add_method_with_wrong_name(self, pulse_sequence: PulseSequence, pulse: Pulse):
        """Test add method with wrong name"""
        pulse.port = pulse_sequence.port
        pulse_sequence.add(pulse=pulse)
        pulse.name = "wrong name"
        with pytest.raises(ValueError):
            pulse_sequence.add(pulse=pulse)

    def test_waveforms_method(self, pulse_sequence: PulseSequence):
        """Test waveforms method."""
        waveforms = pulse_sequence.waveforms(frequency=1e9, resolution=0.1)
        assert isinstance(waveforms.i, np.ndarray) and isinstance(waveforms.q, np.ndarray)

    def test_iter_method(self, pulse_sequence: PulseSequence):
        """Test __iter__ method."""
        for pulse in pulse_sequence:
            assert isinstance(pulse, Pulse)
