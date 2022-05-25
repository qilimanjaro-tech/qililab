"""Pytest configuration fixtures."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_MANAGER_DB, PLATFORM_MANAGER_YAML
from qililab.execution import BusesExecution, BusExecution
from qililab.experiment import Experiment
from qililab.instruments import (
    SGS100A,
    MixerDown,
    MixerUp,
    QbloxPulsarQCM,
    QbloxPulsarQRM,
)
from qililab.platform import Buses, Platform, Qubit, Resonator, Schema
from qililab.pulse import CircuitToPulses, Gaussian, Pulse, PulseSequences

from .data import MockedSettingsHashTable, circuit, experiment_params
from .utils.side_effect import yaml_safe_load_side_effect


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
        ]
    )
    # connect to instrument
    settings = MockedSettingsHashTable.get("qblox_qcm_0")
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
        ]
    )
    # connect to instrument
    settings = MockedSettingsHashTable.get("qblox_qrm_0")
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
    settings = MockedSettingsHashTable.get("rohde_schwarz_0")
    settings.pop("name")
    rohde_schwarz = SGS100A(settings=settings)
    rohde_schwarz.connect()
    return rohde_schwarz


@pytest.fixture(name="qubit")
def fixture_qubit() -> Qubit:
    """Load Qubit.

    Returns:
        Qubit: Instance of the Qubit class.
    """
    qubit_settings = MockedSettingsHashTable.get("resonator_0")["qubits"][0]

    return Qubit(settings=qubit_settings)


@pytest.fixture(name="resonator")
def fixture_resonator() -> Resonator:
    """Load Resonator.

    Returns:
        Resonator: Instance of the Resonator class.
    """
    resonator_settings = MockedSettingsHashTable.get("resonator_0")
    resonator_settings.pop("name")
    return Resonator(settings=resonator_settings)


@pytest.fixture(name="schema")
def fixture_schema(platform: Platform) -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    return platform.schema


@pytest.fixture(name="circuit_to_pulses")
def fixture_circuit_to_pulses() -> CircuitToPulses:
    """Return CircuitToPulses instance."""
    return CircuitToPulses(settings=CircuitToPulses.CircuitToPulsesSettings())


@pytest.fixture(name="pulse_sequence", params=experiment_params)
def fixture_pulse_sequence(circuit_to_pulses: CircuitToPulses) -> PulseSequences:
    """Return PulseSequences instance."""
    return circuit_to_pulses.translate(circuit=circuit)


@pytest.fixture(name="experiment", params=experiment_params)
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment(mock_load: MagicMock, request: pytest.FixtureRequest):
    """Return Experiment object."""
    platform_name, sequences = request.param  # type: ignore
    experiment = Experiment(platform_name=platform_name, sequences=sequences)
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


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db()


def platform_db() -> Platform:
    """Return PlatformBuilderDB instance with loaded platform."""
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")
        mock_load.assert_called()
    return platform


def platform_yaml() -> Platform:
    """Return PlatformBuilderYAML instance with loaded platform."""
    filepath = Path(__file__).parent.parent / "examples" / "all_platform.yml"
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_YAML.build(filepath=str(filepath))
        mock_load.assert_called()
    return platform


def buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")
        mock_load.assert_called()
    return platform.buses


def mixer_up() -> MixerUp:
    """Load Mixer.

    Returns:
        Mixer: Instance of the Mixer class.
    """
    settings = MockedSettingsHashTable.get("mixer_0")
    return MixerUp(settings=settings)


def mixer_down() -> MixerDown:
    """Load Mixer.

    Returns:
        Mixer: Instance of the Mixer class.
    """
    settings = MockedSettingsHashTable.get("mixer_0")
    return MixerDown(settings=settings)
