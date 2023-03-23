"""Tests for the PulseScheduledBus class."""
import pytest

from qililab.execution import PulseScheduledBus
from qililab.pulse import PulseBusSchedule


class TestPulseScheduledBus:
    """Unit tests checking the pulse scheduled bus and methods."""

    def test_add_pulse_method(self, pulse_scheduled_bus: PulseScheduledBus, pulse_bus_schedule: PulseBusSchedule):
        """Test add_pulse method."""
        pulse_scheduled_bus.add_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

    def test_waveforms_method(self, pulse_scheduled_bus: PulseScheduledBus):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1, 10]:
            pulse_scheduled_bus.waveforms(resolution=resolution)

    def test_waveforms_method_raises_error(self, pulse_scheduled_bus: PulseScheduledBus):
        """Test waveforms method raises error."""
        with pytest.raises(IndexError):
            pulse_scheduled_bus.waveforms(idx=10)

    def test_qubit_ids_property(self, pulse_scheduled_bus: PulseScheduledBus):
        """Test qubit_ids property."""
        assert pulse_scheduled_bus.port == pulse_scheduled_bus.bus.port

    def test_acquire_time_method(self, pulse_scheduled_readout_bus: PulseScheduledBus):
        """Test acquire_time method."""
        assert isinstance(pulse_scheduled_readout_bus.acquire_time(), int)  # type: ignore
