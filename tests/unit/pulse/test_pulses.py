"""Tests for the PulseSequences class."""
from qililab.pulse import Pulse, Pulses, ReadoutPulse


class TestPulseSequence:
    """Unit tests checking the PulseSequences attributes and methods"""

    def test_add_method(self, pulses: Pulses, pulse: Pulse, readout_pulse: ReadoutPulse):
        """Test add method."""
        pulses.add(pulse=pulse)
        pulses.add(pulse=readout_pulse)
        pulse.start_time = None
        pulses.add(pulse=pulse)

    def test_to_dict_method(self, pulses: Pulses):
        """Test to_dict method"""
        dictionary = pulses.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, pulses: Pulses):
        """Test from_dict method"""
        dictionary = pulses.to_dict()
        pulse_sequences_2 = Pulses.from_dict(dictionary=dictionary)
        assert isinstance(pulse_sequences_2, Pulses)

    def test_iter_method(self, pulses: Pulses):
        """Test __iter__ method."""
        for pulse in pulses:
            assert isinstance(pulse, Pulse)
