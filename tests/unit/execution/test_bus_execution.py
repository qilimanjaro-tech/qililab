"""Tests for the BusExecution class."""
import pytest

from qililab.execution import BusExecution
from qililab.pulse import Pulse


class TestBusExecution:
    """Unit tests checking the Bus attributes and methods."""

    def test_add_pulse_method(self, bus_execution: BusExecution, pulse: Pulse):
        """Test add_pulse method."""
        bus_execution.add_pulse(pulse=pulse, idx=0)

    def test_add_pulse_method_wrong_idx(self, bus_execution: BusExecution, pulse: Pulse):
        """Test add_pulse method."""
        with pytest.raises(ValueError):
            bus_execution.add_pulse(pulse=pulse, idx=10)

    def test_waveforms_method(self, bus_execution: BusExecution):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1, 10]:
            bus_execution.waveforms(resolution=resolution)

    def test_qubit_ids_property(self, bus_execution: BusExecution):
        """Test qubit_ids property."""
        assert bus_execution.qubit_ids == bus_execution.bus.qubit_ids
