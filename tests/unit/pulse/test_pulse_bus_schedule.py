"""Tests for the PulseSequence class."""
import numpy as np
import pytest

from qililab.pulse import Pulse, PulseBusSchedule, PulseEvent, ReadoutEvent


class TestPulseBusSchedule:
    """Unit tests checking the PulseSequence attributes and methods"""

    def test_add_method(self, pulse_bus_schedule: PulseBusSchedule, pulse: Pulse, start_time: int):
        """Test add method."""
        pulse_bus_schedule.add(pulse=pulse, start_time=start_time)

    def test_add_event_method(self, pulse_bus_schedule: PulseBusSchedule, pulse_event: PulseEvent):
        """Test add method."""
        pulse_bus_schedule.add_event(pulse_event=pulse_event)

    def test_add_event_method_with_wrong_pulse(
        self, pulse_bus_schedule: PulseBusSchedule, pulse_event: PulseEvent, readout_event: ReadoutEvent
    ):
        """Test add method with wrong name"""
        pulse_bus_schedule.add_event(pulse_event=pulse_event)
        with pytest.raises(ValueError):
            pulse_bus_schedule.add_event(pulse_event=readout_event)

    def test_waveforms_method(self, pulse_bus_schedule: PulseBusSchedule):
        """Test waveforms method."""
        waveforms = pulse_bus_schedule.waveforms(frequency=1e9, resolution=0.1)
        assert isinstance(waveforms.i, np.ndarray) and isinstance(waveforms.q, np.ndarray)

    def test_iter_method(self, pulse_bus_schedule: PulseBusSchedule):
        """Test __iter__ method."""
        for pulse in pulse_bus_schedule:
            assert isinstance(pulse, PulseEvent)
