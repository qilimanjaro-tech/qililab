"""Tests for the BusExecution class."""
import numpy as np
import pytest

from qililab.execution import BusExecution, ExecutionManager
from qililab.experiment.experiment import Experiment
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent
from qililab.typings import Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
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
    platform = build_platform(runcard)
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

    def test_acquire_time_raises_error(self, bus_execution: BusExecution):
        """Test that the ``acquire_time`` method raises an error when the index is out of bounds."""
        with pytest.raises(IndexError, match="Index 9 is out of bounds for pulse_schedule list of length"):
            bus_execution.acquire_time(idx=9)
