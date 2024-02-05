"""Tests for the BusExecution class."""
import numpy as np
import pytest

from qililab.execution import BusExecution
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent
from qililab.typings import Parameter
from tests.data import experiment_params
from tests.test_utils import build_platform


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
    return PulseBusSchedule(timeline=[pulse_event], bus_alias="drive_0")


class TestBusExecution:
    """Unit tests checking the BusExecution and methods."""

    def test_add_pulse_method(self, bus_execution: BusExecution, pulse_bus_schedule: PulseBusSchedule):
        """Test add_pulse method."""
        bus_execution.add_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

    def test_waveforms_method(self, bus_execution: BusExecution):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1, 10]:
            bus_execution.waveforms(resolution=resolution)

    def test_waveforms_method_raises_error(self, bus_execution: BusExecution):
        """Test waveforms method raises error."""
        with pytest.raises(IndexError):
            bus_execution.waveforms(idx=10)

    def test_acquire_time_raises_error(self, bus_execution: BusExecution):
        """Test that the ``acquire_time`` method raises an error when the index is out of bounds."""
        with pytest.raises(IndexError, match="Index 9 is out of bounds for pulse_schedule list of length"):
            bus_execution.acquire_time(idx=9)
