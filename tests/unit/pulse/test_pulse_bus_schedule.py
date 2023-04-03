"""Tests for the PulseSequence class."""
import numpy as np
import pytest

from qililab.pulse import Pulse, PulseBusSchedule, PulseEvent, ReadoutEvent


class TestPulseBusSchedule:
    """Unit tests checking the PulseSequence attributes and methods"""

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
        waveforms = pulse_bus_schedule.waveforms(resolution=0.1)
        assert isinstance(waveforms.i, np.ndarray) and isinstance(waveforms.q, np.ndarray)

    def test_iter_method(self, pulse_bus_schedule: PulseBusSchedule):
        """Test __iter__ method."""
        for pulse in pulse_bus_schedule:
            assert isinstance(pulse, PulseEvent)

    def test_unique_pulses_duration(self, pulse_bus_schedule: PulseBusSchedule):
        pulses_duration = sum(pulse.duration for pulse in pulse_bus_schedule.pulses)
        assert pulses_duration == pulse_bus_schedule.unique_pulses_duration

    def test_end(self, pulse_bus_schedule: PulseBusSchedule):
        last_pulse_event = pulse_bus_schedule.timeline[-1]
        end = last_pulse_event.start_time + last_pulse_event.duration
        assert end == pulse_bus_schedule.end

    def test_start(self, pulse_bus_schedule: PulseBusSchedule):
        first_pulse_event = pulse_bus_schedule.timeline[0]
        start = first_pulse_event.start_time
        assert start == pulse_bus_schedule.start

    def test_total_duration(self, pulse_bus_schedule: PulseBusSchedule):
        duration = pulse_bus_schedule.end - pulse_bus_schedule.start
        assert pulse_bus_schedule.duration == duration
