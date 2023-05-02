"""Tests for the PulseSequences class."""
import pytest

from qililab.platform import Platform
from qililab.pulse import CircuitToPulses, PulseBusSchedule, PulseEvent, PulseSchedule
from tests.data import Galadriel, circuit, experiment_params
from tests.utils import platform_db


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=Galadriel.runcard)


@pytest.fixture(name="pulse_schedule", params=experiment_params)
def fixture_pulse_schedule(platform: Platform) -> PulseSchedule:
    """Return PulseSchedule instance."""
    return CircuitToPulses(settings=platform.settings).translate(circuits=[circuit], chip=platform.chip)[0]


class TestPulseSequences:
    """Unit tests checking the PulseSequences attributes and methods"""

    def test_add_event_method(self, pulse_schedule: PulseSchedule, pulse_event: PulseEvent):
        """Tead add_event method."""
        pulse_schedule.add_event(pulse_event=pulse_event, port=0)

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
