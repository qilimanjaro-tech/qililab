"""Tests for the BusExecution class."""
from unittest.mock import MagicMock, patch

import pytest
from qpysequence import Sequence

from qililab.execution import BusExecution, ExecutionManager
from qililab.instruments import AWG
from qililab.pulse import PulseBusSchedule
from tests.utils import mock_instruments


@pytest.fixture(name="pulse_scheduled_readout_bus")
def fixture_pulse_scheduled_readout_bus(execution_manager: ExecutionManager) -> BusExecution:
    """Load PulseScheduledReadoutBus.
    Returns:
        PulseScheduledReadoutBus: Instance of the PulseScheduledReadoutBus class.
    """
    return execution_manager.readout_buses[0]


@pytest.fixture(name="bus_execution")
def fixture_bus_execution(execution_manager: ExecutionManager) -> BusExecution:
    """Load BusExecution.

    Returns:
        BusExecution: Instance of the BusExecution class.
    """
    return execution_manager.buses[0]


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

    def test_alias_property(self, bus_execution: BusExecution):
        """Test alias property."""
        assert bus_execution.alias == bus_execution.bus.alias

    def test_compile(self, bus_execution: BusExecution):
        """Test compile method."""
        sequences = bus_execution.compile(idx=0, nshots=1000, repetition_duration=2000)
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)
        assert sequences[0]._program.duration == 2000 * 1000 + 4  # additional 4ns for the initial wait_sync

    def test_upload(self, bus_execution: BusExecution):
        """Test upload method."""
        awg = bus_execution.system_control.instruments[0]
        assert isinstance(awg, AWG)
        awg.device = MagicMock()
        _ = bus_execution.compile(idx=0, nshots=1000, repetition_duration=2000)
        bus_execution.upload()
        for seq_idx in range(awg.num_sequencers):
            awg.device.sequencers[seq_idx].sequence.assert_called_once()
