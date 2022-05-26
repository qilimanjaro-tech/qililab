"""Tests for the PulseSequences class."""
from qililab.pulse import Pulse, PulseSequences, ReadoutPulse


class TestPulseSequence:
    """Unit tests checking the PulseSequences attributes and methods"""

    def test_add_method(self, pulse_sequences: PulseSequences, pulse: Pulse, readout_pulse: ReadoutPulse):
        """Test add method."""
        pulse_sequences.add(pulse=pulse)
        pulse_sequences.add(pulse=readout_pulse)
        pulse.start_time = None
        pulse_sequences.add(pulse=pulse)

    def test_to_dict_method(self, pulse_sequences: PulseSequences):
        """Test to_dict method"""
        dictionary = pulse_sequences.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, pulse_sequences: PulseSequences):
        """Test from_dict method"""
        dictionary = pulse_sequences.to_dict()
        pulse_sequences_2 = PulseSequences.from_dict(dictionary=dictionary)
        assert isinstance(pulse_sequences_2, PulseSequences)

    def test_iter_method(self, pulse_sequences: PulseSequences):
        """Test __iter__ method."""
        for pulse in pulse_sequences:
            assert isinstance(pulse, Pulse)
