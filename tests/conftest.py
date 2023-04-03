"""Pytest configuration fixtures."""
from unittest.mock import MagicMock, patch

import pytest

from qililab import build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution.execution_buses import PulseScheduledBus
from qililab.execution.execution_manager import ExecutionManager
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.pulse import (
    CircuitToPulses,
    Gaussian,
    Pulse,
    PulseBusSchedule,
    PulseEvent,
    PulseSchedule,
    ReadoutEvent,
    ReadoutPulse,
)
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.typings.loop import LoopOptions
from qililab.utils import Loop

from .data import FluxQubitSimulator, Galadriel, circuit, experiment_params
from .side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db()


@pytest.fixture(name="pulse_schedule", params=experiment_params)
def fixture_pulse_schedule(platform: Platform) -> PulseSchedule:
    """Return PulseSchedule instance."""
    return CircuitToPulses(settings=platform.settings).translate(circuits=[circuit], chip=platform.chip)[0]


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule(pulse_event: PulseEvent) -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return PulseBusSchedule(timeline=[pulse_event], port=0)


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
        alias="X",
        parameter=Parameter.DURATION,
        options=LoopOptions(start=4, stop=1000, step=40),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="nested_experiment", params=experiment_params)
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_nested_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop3 = Loop(
        alias=InstrumentName.QBLOX_QCM.value,
        parameter=Parameter.IF,
        options=LoopOptions(start=0, stop=1, num=2, channel_id=0),
    )
    loop2 = Loop(
        alias="platform",
        parameter=Parameter.DELAY_BEFORE_READOUT,
        options=LoopOptions(start=40, stop=100, step=40),
        loop=loop3,
    )
    loop = Loop(
        alias=InstrumentName.QBLOX_QRM.value,
        parameter=Parameter.GAIN,
        options=LoopOptions(start=0, stop=1, num=2, channel_id=0),
        loop=loop2,
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="execution_manager")
def fixture_execution_manager(experiment: Experiment) -> ExecutionManager:
    """Load ExecutionManager.

    Returns:
        ExecutionManager: Instance of the ExecutionManager class.
    """
    experiment.build_execution()
    return experiment.execution.execution_manager  # pylint: disable=protected-access


@pytest.fixture(name="pulse_scheduled_bus")
def fixture_pulse_scheduled_bus(execution_manager: ExecutionManager) -> PulseScheduledBus:
    """Load PulseScheduledBus.

    Returns:
        PulseScheduledBus: Instance of the PulseScheduledBus class.
    """
    return execution_manager.buses[0]


@pytest.fixture(name="pulse")
def fixture_pulse() -> Pulse:
    """Load Pulse.

    Returns:
        Pulse: Instance of the Pulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="readout_event")
def fixture_readout_event() -> ReadoutEvent:
    """Load ReadoutEvent.

    Returns:
        ReadoutEvent: Instance of the PulseEvent class.
    """
    pulse = ReadoutPulse(amplitude=1, phase=0, duration=50, frequency=1e9)
    return ReadoutEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="simulated_platform")
@patch("qililab.system_control.simulated_system_control.Evolution", autospec=True)
def fixture_simulated_platform(mock_evolution: MagicMock) -> Platform:
    """Return Platform object."""

    # Mocked Evolution needs: system.qubit.frequency, psi0, states, times
    mock_system = MagicMock()
    mock_system.qubit.frequency = 0
    mock_evolution.return_value.system = mock_system
    mock_evolution.return_value.states = []
    mock_evolution.return_value.times = []
    mock_evolution.return_value.psi0 = None

    with patch(
        "qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=FluxQubitSimulator.runcard
    ) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform


def platform_db() -> Platform:
    """Return PlatformBuilderDB instance with loaded platform."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name=DEFAULT_PLATFORM_NAME)
            mock_load.assert_called()
            mock_open.assert_called()
    return platform


def platform_yaml() -> Platform:
    """Return PlatformBuilderYAML instance with loaded platform."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform
