"""Pytest configuration fixtures."""
import copy
from unittest.mock import MagicMock, Mock, patch

import pytest
from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import KeithleyChannel

from qililab import build_platform, load
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import BusesExecution, BusExecution
from qililab.experiment import Experiment
from qililab.instruments import (
    SGS100A,
    Attenuator,
    Keithley2600,
    MixerBasedSystemControl,
    QbloxPulsarQCM,
    QbloxPulsarQRM,
    SimulatedSystemControl,
)
from qililab.platform import Buses, Platform, Qubit, Resonator, Schema
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

from .data import MockedSettingsFactory, circuit, experiment_params
from .side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="qcm")
@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
def fixture_qcm(mock_pulsar: MagicMock):
    """Return connected instance of QbloxPulsarQCM class"""
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
    # connect to instrument
    settings = MockedSettingsFactory.get(platform_name="platform_0", filename="qblox_qcm_0")
    settings.pop("name")
    qcm = QbloxPulsarQCM(settings=settings)
    qcm.connect()
    return qcm


@pytest.fixture(name="qrm")
@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
def fixture_qrm(mock_pulsar: MagicMock):
    """Return connected instance of QbloxPulsarQRM class"""
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
    # connect to instrument
    settings = MockedSettingsFactory.get(platform_name="platform_0", filename="qblox_qrm_0")
    settings.pop("name")
    qrm = QbloxPulsarQRM(settings=settings)
    qrm.connect()
    return qrm


@pytest.fixture(name="rohde_schwarz")
@patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
def fixture_rohde_schwarz(mock_rs: MagicMock):
    """Return connected instance of SGS100A class"""
    # add dynamically created attributes
    mock_instance = mock_rs.return_value
    mock_instance.mock_add_spec(["power", "frequency"])
    # connect to instrument
    settings = MockedSettingsFactory.get(platform_name="platform_0", filename="rohde_schwarz_0")
    settings.pop("name")
    rohde_schwarz = SGS100A(settings=settings)
    rohde_schwarz.connect()
    return rohde_schwarz


@pytest.fixture(name="keithley_2600")
@patch("qililab.instruments.keithley.keithley_2600.Keithley2600Driver", autospec=True)
def fixture_keithley_2600(mock_driver: MagicMock):
    """Return connected instance of Keithley2600 class"""
    # add dynamically created attributes
    mock_instance = mock_driver.return_value
    mock_instance.smua = Mock(KeithleyChannel)
    # connect to instrument
    settings = MockedSettingsFactory.get(platform_name="platform_0", filename="keithley_2600")
    settings.pop("name")
    keithley_2600 = Keithley2600(settings=settings)
    keithley_2600.connect()
    mock_driver.assert_called()
    return keithley_2600


@pytest.fixture(name="qubit")
def fixture_qubit() -> Qubit:
    """Load Qubit.

    Returns:
        Qubit: Instance of the Qubit class.
    """
    qubit_settings = MockedSettingsFactory.get(platform_name="platform_0", filename="resonator_0")["qubits"][0]

    return Qubit(settings=qubit_settings)


@pytest.fixture(name="resonator")
def fixture_resonator() -> Resonator:
    """Load Resonator.

    Returns:
        Resonator: Instance of the Resonator class.
    """
    resonator_settings = MockedSettingsFactory.get(platform_name="platform_0", filename="resonator_0")
    resonator_settings.pop("name")
    return Resonator(settings=resonator_settings)


@pytest.fixture(name="schema")
def fixture_schema(platform: Platform) -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    return platform.schema


@pytest.fixture(name="attenuator")
def fixture_attenuator() -> Attenuator:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    settings = MockedSettingsFactory.get(platform_name="platform_0", filename="attenuator")
    settings.pop("name")
    return Attenuator(settings=settings)


@pytest.fixture(name="pulse_sequences", params=experiment_params)
def fixture_pulse_sequences(platform: Platform) -> PulseSequences:
    """Return PulseSequences instance."""
    return CircuitToPulses().translate(circuit=circuit, translation_settings=platform.translation_settings)


@pytest.fixture(name="pulse_sequence")
def fixture_pulse_sequence(pulse: Pulse) -> PulseSequence:
    """Return PulseSequences instance."""
    return PulseSequence(qubit_ids=[2], pulses=[pulse])


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment_all_platforms(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    platform_name, sequences = request.param  # type: ignore
    platform = build_platform(name=platform_name)
    experiment = Experiment(platform=platform, sequences=sequences)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="experiment", params=experiment_params[:2])
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    platform_name, sequences = request.param  # type: ignore
    platform = build_platform(name=platform_name)
    loop = Loop(
        instrument=Instrument.SIGNAL_GENERATOR,
        id_=0,
        parameter=Parameter.FREQUENCY,
        start=3544000000,
        stop=3744000000,
        num=2,
    )
    experiment = Experiment(platform=platform, sequences=sequences, loop=loop)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="nested_experiment", params=experiment_params[:2])
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_nested_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    platform_name, sequences = request.param  # type: ignore
    platform = build_platform(name=platform_name)
    loop3 = Loop(instrument=Instrument.AWG, id_=0, parameter=Parameter.FREQUENCY, start=0, stop=1, num=2)
    loop2 = Loop(instrument=Instrument.AWG, id_=0, parameter=Parameter.GAIN, start=0, stop=1, step=0.5, loop=loop3)
    loop = Loop(
        instrument=Instrument.SIGNAL_GENERATOR, id_=0, parameter=Parameter.FREQUENCY, start=0, stop=1, num=2, loop=loop2
    )
    experiment = Experiment(platform=platform, sequences=sequences, loop=loop)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="simulated_experiment", params=experiment_params[2:])
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_simulated_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    platform_name, sequences = request.param  # type: ignore
    platform = build_platform(name=platform_name)
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
    return Pulse(amplitude=1, phase=0, duration=50, qubit_ids=[0], pulse_shape=pulse_shape, start_time=0)


@pytest.fixture(name="readout_pulse")
def fixture_readout_pulse() -> ReadoutPulse:
    """Load ReadoutPulse.

    Returns:
        ReadoutPulse: Instance of the ReadoutPulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return ReadoutPulse(amplitude=1, phase=0, duration=50, qubit_ids=[0], pulse_shape=pulse_shape, start_time=0)


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
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = build_platform(name="flux_qubit")
        mock_load.assert_called()
    return platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db()


@pytest.fixture(name="loop")
def fixture_loop() -> Loop:
    """Return Platform object."""
    return Loop(instrument=Instrument.AWG, id_=0, parameter=Parameter.GAIN, start=0, stop=1)


@pytest.fixture(name="pulse_shape", params=[Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, beta=1.0)])
def fixture_pulse_shape(request: pytest.FixtureRequest) -> PulseShape:
    """Return Rectangular object."""
    return request.param  # type: ignore


def platform_db() -> Platform:
    """Return PlatformBuilderDB instance with loaded platform."""
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = build_platform(name=DEFAULT_PLATFORM_NAME)
        mock_load.assert_called()
    return platform


def platform_yaml() -> Platform:
    """Return PlatformBuilderYAML instance with loaded platform."""
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = build_platform(name="platform_0")
        mock_load.assert_called()
    return platform


def buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = build_platform(name="platform_0")
        mock_load.assert_called()
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
