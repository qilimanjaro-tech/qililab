"""Tests for the PulseSequence class."""
import numpy as np
import pytest

from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule(pulse_event: PulseEvent) -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return PulseBusSchedule(bus_alias="readout_bus", timeline=[pulse_event])


@pytest.fixture(name="mux_pulse_bus_schedule")
def fixture_mux_pulse_bus_schedule() -> PulseBusSchedule:
    """Return multiplexed PulseBusSchedule instance."""
    pulse_event_1 = PulseEvent(
        pulse=Pulse(amplitude=1, phase=0.0, duration=1000, frequency=7.0, pulse_shape=Gaussian(num_sigmas=5)),
        start_time=0,
    )
    pulse_event_2 = PulseEvent(
        pulse=Pulse(amplitude=1, phase=0.0, duration=1000, frequency=7.1, pulse_shape=Gaussian(num_sigmas=5)),
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
