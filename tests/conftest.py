"""Pytest configuration fixtures."""
import copy
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest
from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import KeithleyChannel
from qiboconnection.api import API
from qiboconnection.typings.connection import (
    ConnectionConfiguration,
    ConnectionEstablished,
)

from qililab import build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME, RUNCARD, SCHEMA
from qililab.execution import BusesExecution, BusExecution
from qililab.experiment import Experiment
from qililab.instrument_controllers.keithley.keithley_2600_controller import (
    Keithley2600Controller,
)
from qililab.instrument_controllers.mini_circuits.mini_circuits_controller import (
    MiniCircuitsController,
)
from qililab.instrument_controllers.qblox.qblox_pulsar_controller import (
    QbloxPulsarController,
)
from qililab.instrument_controllers.rohde_schwarz.sgs100a_controller import (
    SGS100AController,
)
from qililab.instruments import (
    SGS100A,
    Attenuator,
    Keithley2600,
    MixerBasedSystemControl,
    QbloxQCM,
    QbloxQRM,
    SimulatedSystemControl,
)
from qililab.platform import Buses, Platform, Schema
from qililab.pulse import (
    CircuitToPulses,
    Drag,
    Gaussian,
    Pulse,
    PulseBusSchedule,
    PulseEvent,
    PulseSchedule,
    PulseShape,
    ReadoutEvent,
    ReadoutPulse,
    Rectangular,
)
from qililab.remote_connection.remote_api import RemoteAPI
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.typings.loop import LoopOptions
from qililab.utils import Loop

from .data import (
    FluxQubitSimulator,
    Galadriel,
    circuit,
    experiment_params,
    simulated_experiment_circuit,
)
from .side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db()


@pytest.fixture(name="schema")
def fixture_schema(platform: Platform) -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    return platform.schema


@pytest.fixture(name="pulsar_controller_qcm")
def fixture_pulsar_controller_qcm(platform: Platform):
    """Return an instance of QbloxPulsarController class"""
    settings = copy.deepcopy(Galadriel.pulsar_controller_qcm_0)
    settings.pop("name")
    return QbloxPulsarController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="qcm_no_device")
def fixture_qcm_no_device():
    """Return an instance of QbloxQCM class"""
    settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    settings.pop("name")
    return QbloxQCM(settings=settings)


@pytest.fixture(name="qcm")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
def fixture_qcm(mock_pulsar: MagicMock, pulsar_controller_qcm: QbloxPulsarController):
    """Return connected instance of QbloxQCM class"""
    # add dynamically created attributes
    mock_instance = mock_pulsar.return_value
    mock_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "scope_acq_sequencer_select",
        ]
    )
    mock_instance.sequencers = [mock_instance.sequencer0]
    mock_instance.sequencer0.mock_add_spec(
        [
            "sync_en",
            "gain_awg_path0",
            "gain_awg_path1",
            "sequence",
            "mod_en_awg",
            "nco_freq",
            "scope_acq_sequencer_select",
            "channel_map_path0_out0_en",
            "channel_map_path1_out1_en",
            "demod_en_acq",
            "integration_length_acq",
            "set",
            "offset_awg_path0",
            "offset_awg_path1",
        ]
    )
    pulsar_controller_qcm.connect()
    return pulsar_controller_qcm.modules[0]


@pytest.fixture(name="pulsar_controller_qrm")
def fixture_pulsar_controller_qrm(platform: Platform):
    """Return an instance of QbloxPulsarController class"""
    settings = copy.deepcopy(Galadriel.pulsar_controller_qrm_0)
    settings.pop("name")
    return QbloxPulsarController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="qrm_no_device")
def fixture_qrm_no_device():
    """Return an instance of QbloxQRM class"""
    settings = copy.deepcopy(Galadriel.qblox_qrm_0)
    settings.pop("name")
    return QbloxQRM(settings=settings)


@pytest.fixture(name="qrm")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
def fixture_qrm(mock_pulsar: MagicMock, pulsar_controller_qrm: QbloxPulsarController):
    """Return connected instance of QbloxQRM class"""
    # add dynamically created attributes
    mock_instance = mock_pulsar.return_value
    mock_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "scope_acq_sequencer_select",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
        ]
    )
    mock_instance.sequencers = [mock_instance.sequencer0, mock_instance.sequencer0]
    mock_instance.sequencer0.mock_add_spec(
        [
            "sync_en",
            "gain_awg_path0",
            "gain_awg_path1",
            "sequence",
            "mod_en_awg",
            "nco_freq",
            "scope_acq_sequencer_select",
            "channel_map_path0_out0_en",
            "channel_map_path1_out1_en",
            "demod_en_acq",
            "integration_length_acq",
            "set",
            "offset_awg_path0",
            "offset_awg_path1",
        ]
    )
    # connect to instrument
    pulsar_controller_qrm.connect()
    return pulsar_controller_qrm.modules[0]


@pytest.fixture(name="rohde_schwarz_controller")
def fixture_rohde_schwarz_controller(platform: Platform):
    """Return an instance of SGS100A controller class"""
    settings = copy.deepcopy(Galadriel.rohde_schwarz_controller_0)
    settings.pop("name")
    return SGS100AController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="rohde_schwarz_no_device")
def fixture_rohde_schwarz_no_device():
    """Return an instance of SGS100A class"""
    settings = copy.deepcopy(Galadriel.rohde_schwarz_0)
    settings.pop("name")
    return SGS100A(settings=settings)


@pytest.fixture(name="rohde_schwarz")
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
def fixture_rohde_schwarz(mock_rs: MagicMock, rohde_schwarz_controller: SGS100AController):
    """Return connected instance of SGS100A class"""
    # add dynamically created attributes
    mock_instance = mock_rs.return_value
    mock_instance.mock_add_spec(["power", "frequency"])
    rohde_schwarz_controller.connect()
    return rohde_schwarz_controller.modules[0]


@pytest.fixture(name="keithley_2600_controller")
def fixture_keithley_2600_controller(platform: Platform):
    """Return connected instance of Keithley2600Controller class"""
    settings = copy.deepcopy(Galadriel.keithley_2600_controller_0)
    settings.pop("name")
    return Keithley2600Controller(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="keithley_2600_no_device")
def fixture_keithley_2600_no_device():
    """Return connected instance of Keithley2600 class"""
    settings = copy.deepcopy(Galadriel.keithley_2600)
    settings.pop("name")
    return Keithley2600(settings=settings)


@pytest.fixture(name="keithley_2600")
@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
def fixture_keithley_2600(mock_driver: MagicMock, keithley_2600_controller: Keithley2600Controller):
    """Return connected instance of Keithley2600 class"""
    mock_instance = mock_driver.return_value
    mock_instance.smua = MagicMock(KeithleyChannel)
    mock_instance.smua.mock_add_spec(["limiti", "limitv", "doFastSweep"])
    keithley_2600_controller.connect()
    mock_driver.assert_called()
    return keithley_2600_controller.modules[0]


@pytest.fixture(name="attenuator_controller")
def fixture_attenuator_controller(platform: Platform) -> MiniCircuitsController:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    settings = copy.deepcopy(Galadriel.attenuator_controller_0)
    settings.pop("name")
    return MiniCircuitsController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="attenuator_no_device")
def fixture_attenuator_no_device() -> Attenuator:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    settings = copy.deepcopy(Galadriel.attenuator)
    settings.pop("name")
    return Attenuator(settings=settings)


@pytest.fixture(name="attenuator")
@patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
def fixture_attenuator(mock_urllib: MagicMock, attenuator_controller: MiniCircuitsController) -> Attenuator:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    attenuator_controller.connect()
    mock_urllib.request.Request.assert_called()
    mock_urllib.request.urlopen.assert_called()
    return attenuator_controller.modules[0]


@pytest.fixture(name="pulse_schedule", params=experiment_params)
def fixture_pulse_schedule(platform: Platform) -> PulseSchedule:
    """Return PulseSchedule instance."""
    return CircuitToPulses(settings=platform.settings).translate(circuits=[circuit], chip=platform.chip)[0]


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule(pulse_event: PulseEvent) -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return PulseBusSchedule(timeline=[pulse_event], port=0)


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment_all_platforms(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, schedules = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    experiment = Experiment(platform=platform, schedules=schedules)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="experiment", params=experiment_params)
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, schedules = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="rs_0",
        parameter=Parameter.FREQUENCY,
        options=LoopOptions(
            start=3544000000,
            stop=3744000000,
            num=10,
        ),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(platform=platform, schedules=schedules, options=options)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="experiment_reset", params=experiment_params)
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment_reset(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, schedules = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            mock_load.return_value[RUNCARD.SCHEMA][SCHEMA.INSTRUMENT_CONTROLLERS][0] |= {"reset": False}
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="rs_0",
        parameter=Parameter.FREQUENCY,
        options=LoopOptions(
            start=3544000000,
            stop=3744000000,
            num=2,
        ),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(platform=platform, schedules=schedules, options=options)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="nested_experiment", params=experiment_params)
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_nested_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, schedules = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    loop3 = Loop(
        alias=InstrumentName.QBLOX_QCM.value,
        parameter=Parameter.FREQUENCIES,
        options=LoopOptions(start=0, stop=1, num=2),
    )
    loop2 = Loop(
        alias="platform",
        parameter=Parameter.DELAY_BEFORE_READOUT,
        options=LoopOptions(start=40, stop=100, step=40),
        loop=loop3,
    )
    loop = Loop(
        alias=InstrumentName.ROHDE_SCHWARZ.value,
        parameter=Parameter.FREQUENCIES,
        options=LoopOptions(start=0, stop=1, num=2),
        loop=loop2,
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(platform=platform, schedules=schedules, options=options)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="simulated_experiment")
def fixture_simulated_experiment(simulated_platform: Platform):
    """Return Experiment object."""
    return Experiment(platform=simulated_platform, schedules=simulated_experiment_circuit)


@pytest.fixture(name="buses_execution")
def fixture_buses_execution(experiment: Experiment) -> BusesExecution:
    """Load BusesExecution.

    Returns:
        BusesExecution: Instance of the BusesExecution class.
    """
    return experiment.execution.buses_execution


@pytest.fixture(name="bus_execution")
def fixture_bus_execution(buses_execution: BusesExecution) -> BusExecution:
    """Load BusExecution.

    Returns:
        BusExecution: Instance of the BusExecution class.
    """
    return buses_execution.buses[0]


@pytest.fixture(name="pulse")
def fixture_pulse() -> Pulse:
    """Load Pulse.

    Returns:
        Pulse: Instance of the Pulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return Pulse(amplitude=1, phase=0, duration=50, pulse_shape=pulse_shape)


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="readout_event")
def fixture_readout_event() -> ReadoutEvent:
    """Load ReadoutEvent.

    Returns:
        ReadoutEvent: Instance of the PulseEvent class.
    """
    pulse = ReadoutPulse(amplitude=1, phase=0, duration=50)
    return ReadoutEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="readout_pulse")
def fixture_readout_pulse() -> ReadoutPulse:
    """Load ReadoutPulse.

    Returns:
        ReadoutPulse: Instance of the ReadoutPulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return ReadoutPulse(amplitude=1, phase=0, duration=50, pulse_shape=pulse_shape)


@pytest.fixture(name="mixer_based_system_control")
def fixture_mixer_based_system_control(platform: Platform) -> MixerBasedSystemControl:
    """Load SimulatedSystemControl.

    Returns:
        SimulatedSystemControl: Instance of the SimulatedSystemControl class.
    """
    return platform.buses[0].system_control


@pytest.fixture(name="simulated_system_control")
def fixture_simulated_system_control(simulated_platform: Platform) -> SimulatedSystemControl:
    """Load SimulatedSystemControl.

    Returns:
        SimulatedSystemControl: Instance of the SimulatedSystemControl class.
    """
    return simulated_platform.buses[0].system_control


@pytest.fixture(name="simulated_platform")
@patch("qililab.instruments.system_control.simulated_system_control.Evolution", autospec=True)
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


@pytest.fixture(name="loop")
def fixture_loop() -> Loop:
    """Return Platform object."""
    return Loop(alias="X", parameter=Parameter.AMPLITUDE, options=LoopOptions(start=0, stop=1))


@pytest.fixture(
    name="pulse_shape", params=[Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]
)
def fixture_pulse_shape(request: pytest.FixtureRequest) -> PulseShape:
    """Return Rectangular object."""
    return request.param  # type: ignore


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
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform


def buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform.buses


def mock_instruments(mock_rs: MagicMock, mock_pulsar: MagicMock, mock_keithley: MagicMock):
    """Mock dynamically created attributes."""
    mock_rs_instance = mock_rs.return_value
    mock_rs_instance.mock_add_spec(["power", "frequency"])
    mock_pulsar_instance = mock_pulsar.return_value
    mock_pulsar_instance.get_acquisitions.side_effect = lambda sequencer: copy.deepcopy(
        {
            "single": {
                "index": 0,
                "acquisition": {
                    "scope": {
                        "path0": {"data": [1, 1, 1, 1, 1, 1, 1, 1], "out-of-range": False, "avg_cnt": 1000},
                        "path1": {"data": [0, 0, 0, 0, 0, 0, 0, 0], "out-of-range": False, "avg_cnt": 1000},
                    },
                    "bins": {
                        "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                        "threshold": [0.48046875],
                        "avg_cnt": [1024],
                    },
                },
            }
        }
    )
    mock_pulsar_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "sequencers",
            "scope_acq_sequencer_select",
        ]
    )
    mock_pulsar_instance.sequencer0.mock_add_spec(
        [
            "sync_en",
            "gain_awg_path0",
            "gain_awg_path1",
            "sequence",
            "mod_en_awg",
            "nco_freq",
            "scope_acq_sequencer_select",
            "channel_map_path0_out0_en",
            "channel_map_path1_out1_en",
            "demod_en_acq",
            "integration_length_acq",
            "offset_awg_path0",
            "offset_awg_path1",
        ]
    )
    mock_keithley_instance = mock_keithley.return_value
    mock_keithley_instance.smua = MagicMock(KeithleyChannel)
    mock_keithley_instance.smua.mock_add_spec(["limiti", "limitv", "doFastSweep"])


@pytest.fixture(scope="session", name="mocked_connection_configuration")
def fixture_create_mocked_connection_configuration() -> ConnectionConfiguration:
    """Create a mock connection configuration"""
    return ConnectionConfiguration(user_id=666, username="mocked_user", api_key="betterNOTaskMockedAPIKey")


@pytest.fixture(scope="session", name="mocked_connection_established")
def fixture_create_mocked_connection_established(
    mocked_connection_configuration: ConnectionConfiguration,
) -> ConnectionEstablished:
    """Create a mock connection configuration"""
    return ConnectionEstablished(
        **asdict(mocked_connection_configuration),
        authorisation_access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3O"
        + "DkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        api_path="/api/v1",
    )


@pytest.fixture(scope="session", name="mocked_api")
def fixture_create_mocked_api_connection(mocked_connection_established: ConnectionEstablished) -> API:
    """Create a mocked api connection
    Returns:
        API: API mocked connection
    """
    with patch(
        "qiboconnection.connection.load_config_file_to_disk",
        autospec=True,
        return_value=mocked_connection_established,
    ) as mock_config:
        api = API()
        mock_config.assert_called()
        return api


@pytest.fixture(name="mocked_remote_api")
def fixtuer_create_mocked_remote_api(mocked_api: API) -> RemoteAPI:
    """Create a mocked remote api connection
    Returns:
        RemoteAPI: Remote API mocked connection
    """
    return RemoteAPI(connection=mocked_api)


@pytest.fixture(name="valid_remote_api")
def fixtuer_create_valid_remote_api() -> RemoteAPI:
    """Create a valid remote api connection
    Returns:
        RemoteAPI: Remote API connection
    """
    configuration = ConnectionConfiguration(
        username="write-a-valid-user",
        api_key="write-a-valid-key",
    )
    return RemoteAPI(connection=API(configuration=configuration))


@pytest.fixture(name="second_valid_remote_api")
def fixtuer_create_second_valid_remote_api() -> RemoteAPI:
    """Create a valid remote api connection
    Returns:
        RemoteAPI: Remote API connection
    """
    configuration = ConnectionConfiguration(
        username="write-a-valid-user",
        api_key="write-a-valid-key",
    )
    return RemoteAPI(connection=API(configuration=configuration))
