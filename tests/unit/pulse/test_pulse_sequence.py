"""Tests for the PulseSequence class."""
import pytest

from qililab.pulse import Pulse, PulseSequence


class TestPulseSequence:
    """Unit tests checking the PulseSequence attributes and methods"""

    def test_add_method(self, pulse_sequence: PulseSequence, pulse: Pulse):
        """Test add method."""
        pulse.qubit_ids = pulse_sequence.qubit_ids
        pulse_sequence.add(pulse=pulse)

    def test_add_method_with_wrong_qubit_ids(self, pulse_sequence: PulseSequence, pulse: Pulse):
        """Test add method with wrong qubit_ids"""
        pulse.qubit_ids = [1, 23, 5]
        with pytest.raises(ValueError):
            pulse_sequence.add(pulse=pulse)

    def test_add_method_with_wrong_name(self, pulse_sequence: PulseSequence, pulse: Pulse):
        """Test add method with wrong name"""
        pulse.qubit_ids = pulse_sequence.qubit_ids
        pulse_sequence.add(pulse=pulse)
        pulse.name = "wrong name"
        with pytest.raises(ValueError):
            pulse_sequence.add(pulse=pulse)

    def test_waveforms_method(self, pulse_sequence: PulseSequence):
        """Test waveforms method."""
        waveforms_i, waveforms_q = pulse_sequence.waveforms(frequency=1e9, resolution=0.1)
        assert isinstance(waveforms_i, list) and isinstance(waveforms_q, list)

    def test_iter_method(self, pulse_sequence: PulseSequence):
        """Test __iter__ method."""
        for pulse in pulse_sequence:
            assert isinstance(pulse, Pulse)
