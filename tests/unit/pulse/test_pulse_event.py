"""Tests for the Pulse class."""
import numpy as np
import pytest

from qililab.pulse import Pulse, PulseEvent
from qililab.utils import Waveforms


class TestPulseEvent:
    """Unit tests checking the PulseEvent attributes and methods"""

    def test_modulated_waveforms_method(self, pulse_event: PulseEvent):
        """Test modulated_waveforms method."""
        waveforms = pulse_event.modulated_waveforms()
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse_event: PulseEvent):
        """Test envelope method"""
        for pulse in pulse_event.pulses:
            envelope = pulse.envelope(amplitude=2.0, resolution=0.1)
            assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse_event: PulseEvent):
        """Test to_dict method"""
        dictionary = pulse_event.to_dict()
        assert isinstance(dictionary, dict)

    def test_merge_method(self, pulse_event: PulseEvent, pulse: Pulse):
        """Test merge method."""
        start_time = pulse_event.start_time
        event_sync = PulseEvent(pulses=[pulse], start_time=start_time)
        event_unsync = PulseEvent(pulses=[pulse], start_time=start_time + 1)
        event_length_original = len(pulse_event.pulses)
        with pytest.raises(ValueError):
            pulse_event.merge(pulse_event=event_unsync)
        assert len(pulse_event.pulses) == event_length_original
        pulse_event.merge(event_sync)
        assert len(pulse_event.pulses) == event_length_original + 1
