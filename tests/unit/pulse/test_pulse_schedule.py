"""Tests for the PulseSequences class."""
import pytest

from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent, PulseSchedule, ReadoutEvent, ReadoutPulse


@pytest.fixture(name="readout_pulse")
def fixture_readout_pulse() -> ReadoutPulse:
    """Load ReadoutPulse.

    Returns:
        ReadoutPulse: Instance of the ReadoutPulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return ReadoutPulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)


class TestPulseSequences:
    """Unit tests checking the PulseSequences attributes and methods"""

    def test_add_method(
        self,
        pulse_schedule: PulseSchedule,
        pulse: Pulse,
        readout_pulse: ReadoutPulse,
    ):
        """Test add method."""
        pulse_schedule.add(pulse=pulse, start_time=0, port=0)
        pulse_schedule.add(pulse=readout_pulse, start_time=2000, port=1)

    def test_add_event_method(
        self, pulse_schedule: PulseSchedule, pulse_event: PulseEvent, readout_event: ReadoutEvent
    ):
        """Tead add_event method."""
        pulse_schedule.add_event(pulse_event=pulse_event, port=0)
        pulse_schedule.add_event(pulse_event=readout_event, port=1)

    def test_to_dict_method(self, pulse_schedule: PulseSchedule):
        """Test to_dict method"""
        dictionary = pulse_schedule.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, pulse_schedule: PulseSchedule):
        """Test from_dict method"""
        dictionary = pulse_schedule.to_dict()
        pulse_schedule_2 = PulseSchedule.from_dict(dictionary=dictionary)
        assert isinstance(pulse_schedule_2, PulseSchedule)

    def test_iter_method(self, pulse_schedule: PulseSchedule):
        """Test __iter__ method."""
        for pulse_bus_schedule in pulse_schedule:
            assert isinstance(pulse_bus_schedule, PulseBusSchedule)
