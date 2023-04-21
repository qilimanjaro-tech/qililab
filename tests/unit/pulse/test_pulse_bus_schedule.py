"""Tests for the PulseSequence class."""
import numpy as np
import pytest

from qililab.circuit import GaussianPulse
from qililab.pulse import PulseBusSchedule, PulseEvent


@pytest.fixture(name="mux_pulse_bus_schedule")
def fixture_mux_pulse_bus_schedule() -> PulseBusSchedule:
    """Return multiplexed PulseBusSchedule instance."""
    pulse_event_1 = PulseEvent(
        pulse=GaussianPulse(amplitude=1.0, phase=0, duration=50, frequency=1e9, sigma=4),
        start_time=0,
    )
    pulse_event_2 = PulseEvent(
        pulse=GaussianPulse(amplitude=1.0, phase=0, duration=50, frequency=1e9, sigma=4),
        start_time=0,
    )
    return PulseBusSchedule(timeline=[pulse_event_1, pulse_event_2], port=0)


class TestPulseBusSchedule:
    """Unit tests checking the PulseSequence attributes and methods"""

    def test_add_event_method(self, pulse_bus_schedule: PulseBusSchedule, pulse_event: PulseEvent):
        """Test add method."""
        pulse_bus_schedule.add_event(pulse_event=pulse_event)

    def test_waveforms_method(self, pulse_bus_schedule: PulseBusSchedule):
        """Test waveforms method."""
        waveforms = pulse_bus_schedule.waveforms(resolution=0.1)
        assert isinstance(waveforms.i, np.ndarray) and isinstance(waveforms.q, np.ndarray)

    def test_iter_method(self, pulse_bus_schedule: PulseBusSchedule):
        """Test __iter__ method."""
        for pulse in pulse_bus_schedule:
            assert isinstance(pulse, PulseEvent)

    def test_unique_pulses_duration(self, pulse_bus_schedule: PulseBusSchedule):
        """Test the unique_pulses_duration property."""
        pulses_duration = sum(pulse.duration for pulse in pulse_bus_schedule.pulses)
        assert pulses_duration == pulse_bus_schedule.unique_pulses_duration

    def test_end(self, pulse_bus_schedule: PulseBusSchedule):
        """Test the end_time property."""
        last_pulse_event = pulse_bus_schedule.timeline[-1]
        end = last_pulse_event.start_time + last_pulse_event.pulse.duration
        assert end == pulse_bus_schedule.end_time

    def test_start(self, pulse_bus_schedule: PulseBusSchedule):
        """Test the start_time property."""
        first_pulse_event = pulse_bus_schedule.timeline[0]
        start = first_pulse_event.start_time
        assert start == pulse_bus_schedule.start_time

    def test_total_duration(self, pulse_bus_schedule: PulseBusSchedule):
        """Test the total duration property."""
        duration = pulse_bus_schedule.end_time - pulse_bus_schedule.start_time
        assert pulse_bus_schedule.duration == duration

    def test_frequencies(self, mux_pulse_bus_schedule: PulseBusSchedule):
        """Test the frequencies method."""
        frequencies = sorted({event.frequency for event in mux_pulse_bus_schedule.timeline})
        assert frequencies == mux_pulse_bus_schedule.frequencies()

    def test_with_frequency(self, mux_pulse_bus_schedule: PulseBusSchedule):
        """Test the with_frequency method."""
        frequencies = mux_pulse_bus_schedule.frequencies()
        for frequency in frequencies:
            schedule = mux_pulse_bus_schedule.with_frequency(frequency)
            assert len(schedule.frequencies()) == 1
            assert frequency == schedule.frequencies()[0]
