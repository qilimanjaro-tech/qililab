"""Tests for the PulseScheduledBus class."""
import pytest

from qililab.execution import PulseScheduledBus
from qililab.execution.execution_manager import ExecutionManager
from qililab.pulse import PulseBusSchedule


@pytest.fixture(name="pulse_scheduled_bus")
def fixture_pulse_scheduled_bus(execution_manager: ExecutionManager) -> PulseScheduledBus:
    """Load PulseScheduledBus.

    Returns:
        PulseScheduledBus: Instance of the PulseScheduledBus class.
    """
    return execution_manager.buses[0]


@pytest.fixture(name="pulse_scheduled_readout_bus")
def fixture_pulse_scheduled_readout_bus(execution_manager: ExecutionManager) -> PulseScheduledBus:
    """Load PulseScheduledReadoutBus.

    Returns:
        PulseScheduledReadoutBus: Instance of the PulseScheduledReadoutBus class.
    """
    return execution_manager.readout_buses[0]


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

    def test_acquire_time_raises_error(self, pulse_scheduled_bus: PulseScheduledBus):
        """Test that the ``acquire_time`` method raises an error when the index is out of bounds."""
        with pytest.raises(IndexError, match="Index 9 is out of bounds for pulse_schedule list of length"):
            pulse_scheduled_bus.acquire_time(idx=9)

    def test_acquire_results_raises_error(self, pulse_scheduled_bus: PulseScheduledBus):
        """Test that the ``acquire_results`` raises an error when no readout system control is present."""
        with pytest.raises(
            ValueError, match="The bus drive_line_bus needs a readout system control to acquire the results"
        ):
            pulse_scheduled_bus.acquire_result()
