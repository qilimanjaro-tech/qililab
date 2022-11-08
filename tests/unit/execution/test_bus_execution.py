"""Tests for the BusExecution class."""
import pytest

from qililab.execution import BusExecution
from qililab.pulse import PulseBusSchedule


class TestBusExecution:
    """Unit tests checking the Bus attributes and methods."""

    def test_add_pulse_method(self, bus_execution: BusExecution, pulse_sequence: PulseBusSchedule):
        """Test add_pulse method."""
        pulse_sequence.pulses[0].frequency = bus_execution.pulse_sequences[0].frequency
        bus_execution.add_pulse_sequence(pulse_sequence=pulse_sequence)

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

    def test_acquire_time_method(self, buses_execution: BusExecution):
        """Test acquire_time method."""
        assert isinstance(buses_execution[1].acquire_time(), int)  # type: ignore

    def test_acquire_time_method_raises_error(self, buses_execution: BusExecution):
        """Test acquire_time method."""
        with pytest.raises(ValueError):
            buses_execution[0].acquire_time()  # type: ignore
