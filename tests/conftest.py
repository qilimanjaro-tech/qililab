"""Pytest configuration fixtures."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_MANAGER_DB, PLATFORM_MANAGER_YAML
from qililab.constants import DEFAULT_PLATFORM_NAME, DEFAULT_SETTINGS_FOLDERNAME
from qililab.experiment import Experiment
from qililab.instruments import (
    SGS100A,
    MixerDown,
    MixerUp,
    QbloxPulsarQCM,
    QbloxPulsarQRM,
)
from qililab.platform import Buses, Platform, Qubit, Resonator, Schema
from qililab.pulse import Pulse, PulseSequences, ReadoutPulse
from qililab.pulse.pulse_shape import Drag
from qililab.settings import SETTINGS_MANAGER

from .data import (
    MockedSettingsHashTable,
    mixer_0_settings_sample,
    qblox_qcm_0_settings_sample,
    qblox_qrm_0_settings_sample,
    rohde_schwarz_0_settings_sample,
)
from .utils.side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="qcm")
@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
@patch("qililab.settings.settings_manager.yaml.safe_load", return_value=qblox_qcm_0_settings_sample)
def fixture_qcm(mock_load: MagicMock, mock_pulsar: MagicMock):
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
    qcm_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="qblox_qcm_0"
    )
    settings = qcm_settings.copy()
    settings.pop("name")
    mock_load.assert_called_once()
    qcm = QbloxPulsarQCM(settings=settings)
    qcm.connect()
    return qcm


@pytest.fixture(name="qrm")
@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
@patch("qililab.settings.settings_manager.yaml.safe_load", return_value=qblox_qrm_0_settings_sample)
def fixture_qrm(mock_load: MagicMock, mock_pulsar: MagicMock):
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
    qrm_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="qblox_qrm_0"
    )
    settings = qrm_settings.copy()
    settings.pop("name")
    mock_load.assert_called_once()
    qrm = QbloxPulsarQRM(settings=settings)
    qrm.connect()
    return qrm


@pytest.fixture(name="rohde_schwarz")
@patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.settings.settings_manager.yaml.safe_load", return_value=rohde_schwarz_0_settings_sample)
def fixture_rohde_schwarz(mock_load: MagicMock, mock_rs: MagicMock):
    """Return connected instance of SGS100A class"""
    # add dynamically created attributes
    mock_instance = mock_rs.return_value
    mock_instance.mock_add_spec(["power", "frequency"])
    # connect to instrument
    rohde_schwarz_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="rohde_schwarz_0"
    )
    settings = rohde_schwarz_settings.copy()
    settings.pop("name")
    mock_load.assert_called_once()
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
def fixture_schema() -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    return platform_db().schema


@pytest.fixture(name="experiment")
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment(mock_load: MagicMock):
    """Return Experiment object."""
    pulse_sequence = PulseSequences(delay_between_pulses=0, delay_before_readout=50)
    pulse_sequence.add(Pulse(amplitude=1, phase=0, pulse_shape=Drag(num_sigmas=4, beta=1), duration=50, qubit_ids=[0]))
    pulse_sequence.add(ReadoutPulse(amplitude=1, phase=0, duration=50, qubit_ids=[0]))

    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=[pulse_sequence, pulse_sequence])
    mock_load.assert_called()
    return experiment


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
    settings = mixer_0_settings_sample.copy()
    return MixerUp(settings=settings)


def mixer_down() -> MixerDown:
    """Load Mixer.

    Returns:
        Mixer: Instance of the Mixer class.
    """
    settings = mixer_0_settings_sample.copy()
    return MixerDown(settings=settings)
