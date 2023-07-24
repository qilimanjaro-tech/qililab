"""Tests for the BusExecution class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qpysequence import Sequence

from qililab import build_platform
from qililab.execution import BusExecution, ExecutionManager
from qililab.experiment.experiment import Experiment
from qililab.instruments import AWG
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent
from qililab.typings import Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import experiment_params
from tests.utils import mock_instruments


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="execution_manager")
def fixture_execution_manager(experiment: Experiment) -> ExecutionManager:
    """Load ExecutionManager.

    Returns:
        ExecutionManager: Instance of the ExecutionManager class.
    """
    experiment.build_execution()
    return experiment.execution_manager  # pylint: disable=protected-access


@pytest.fixture(name="experiment", params=experiment_params)
def fixture_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="X(0)",
        parameter=Parameter.DURATION,
        values=np.arange(start=4, stop=1000, step=40),
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule(pulse_event: PulseEvent) -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return PulseBusSchedule(timeline=[pulse_event], port=0)


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
        sequences = bus_execution.compile(idx=0, nshots=1000, repetition_duration=2000, num_bins=1)
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)
        assert sequences[0]._program.duration == 2000 * 1000 + 4  # additional 4ns for the initial wait_sync

    def test_upload(self, bus_execution: BusExecution):
        """Test upload method."""
        awg = bus_execution.system_control.instruments[0]
        assert isinstance(awg, AWG)
        awg.device = MagicMock()
        _ = bus_execution.compile(idx=0, nshots=1000, repetition_duration=2000, num_bins=1)
        bus_execution.upload()
        for seq_idx in range(awg.num_sequencers):
            awg.device.sequencers[seq_idx].sequence.assert_called_once()
