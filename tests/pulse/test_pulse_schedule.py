"""Tests for the PulseSequences class."""
import pytest

from qililab.circuit_transpiler import CircuitTranspiler
from qililab.data_management import build_platform
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent, PulseSchedule
from tests.data import Galadriel, circuit, experiment_params


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="pulse_schedule", params=experiment_params)
def fixture_pulse_schedule(platform: Platform) -> PulseSchedule:
    """Return PulseSchedule instance."""
    return CircuitTranspiler(gates_settings=platform.gates_settings).circuit_to_pulses(circuits=[circuit])[0]


class TestPulseSequences:
    """Unit tests checking the PulseSequences attributes and methods"""

    def test_add_event_method(self, pulse_schedule: PulseSchedule, pulse_event: PulseEvent):
        """Tead add_event method."""
        pulse_schedule.add_event(pulse_event=pulse_event, bus_alias="drive_q0", delay=0)

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
