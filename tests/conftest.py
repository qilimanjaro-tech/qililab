"""Pytest configuration fixtures."""
import copy
from unittest.mock import MagicMock, patch

import pytest
from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import KeithleyChannel

from qililab import build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
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
    PulseSequence,
    PulseSequences,
    PulseShape,
    ReadoutPulse,
    Rectangular,
)
from qililab.typings import Instrument, Parameter
from qililab.utils import Loop

from .data import FluxQubitSimulator, Galadriel, circuit, experiment_params
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


@pytest.fixture(name="pulse_sequences", params=experiment_params)
def fixture_pulses(platform: Platform) -> PulseSequences:
    """Return Pulses instance."""
    return CircuitToPulses(settings=platform.settings).translate(circuits=[circuit], chip=platform.chip)[0]


@pytest.fixture(name="pulse_sequence")
def fixture_pulse_sequence(pulse: Pulse) -> PulseSequence:
    """Return PulseSequences instance."""
    return PulseSequence(pulses=[pulse], port=0)


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment_all_platforms(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, sequences = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    experiment = Experiment(platform=platform, sequences=sequences)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="experiment", params=experiment_params[:2])
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, sequences = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="rs_0",
        parameter=Parameter.FREQUENCY,
        start=3544000000,
        stop=3744000000,
        num=2,
    )
    experiment = Experiment(platform=platform, sequences=sequences, loop=loop)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="nested_experiment", params=experiment_params[:2])
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_nested_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, sequences = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    loop3 = Loop(instrument=Instrument.AWG, id_=0, parameter=Parameter.FREQUENCY, start=0, stop=1, num=2)
    loop2 = Loop(alias="platform", parameter=Parameter.DELAY_BEFORE_READOUT, start=40, stop=100, step=40, loop=loop3)
    loop = Loop(
        instrument=Instrument.SIGNAL_GENERATOR, id_=0, parameter=Parameter.FREQUENCY, start=0, stop=1, num=2, loop=loop2
    )
    experiment = Experiment(platform=platform, sequences=sequences, loop=loop)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="simulated_experiment", params=experiment_params[2:])
@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_simulated_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, sequences = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    experiment = Experiment(platform=platform, sequences=sequences)
    mock_load.assert_called()
    return experiment


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
    return Pulse(amplitude=1, phase=0, duration=50, pulse_shape=pulse_shape, start_time=0)


@pytest.fixture(name="readout_pulse")
def fixture_readout_pulse() -> ReadoutPulse:
    """Load ReadoutPulse.

    Returns:
        ReadoutPulse: Instance of the ReadoutPulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return ReadoutPulse(amplitude=1, phase=0, duration=50, pulse_shape=pulse_shape, start_time=0)


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
def fixture_simulated_platform() -> Platform:
    """Return Platform object."""
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
    return Loop(alias="X", parameter=Parameter.AMPLITUDE, start=0, stop=1)


@pytest.fixture(name="pulse_shape", params=[Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, beta=1.0)])
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


def mock_instruments(mock_rs: MagicMock, mock_pulsar: MagicMock):
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
                        "integration": {"path0": [1, 1, 1, 1], "path1": [0, 0, 0, 0]},
                        "threshold": [0.5, 0.5, 0.5, 0.5],
                        "avg_cnt": [1000, 1000, 1000, 1000],
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
