"""Tests for the BusExecution class."""
import pytest

from qililab.execution import BusExecution
from qililab.pulse import PulseBusSchedule


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

    def test_qubit_ids_property(self, bus_execution: BusExecution):
        """Test qubit_ids property."""
        assert bus_execution.port == bus_execution.bus.port

    def test_acquire_time_method(self, pulse_scheduled_readout_bus: BusExecution):
        """Test acquire_time method."""
        assert isinstance(pulse_scheduled_readout_bus.acquire_time(), int)  # type: ignore

    def test_acquire_time_raises_error(self, bus_execution: BusExecution):
        """Test that the ``acquire_time`` method raises an error when the index is out of bounds."""
        with pytest.raises(IndexError, match="Index 9 is out of bounds for pulse_schedule list of length"):
            bus_execution.acquire_time(idx=9)

    def test_acquire_results_raises_error(self, bus_execution: BusExecution):
        """Test that the ``acquire_results`` raises an error when no readout system control is present."""
        with pytest.raises(
            ValueError, match="The bus drive_line_bus needs a readout system control to acquire the results"
        ):
            bus_execution.acquire_result()
