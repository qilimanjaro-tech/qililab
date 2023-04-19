"""Test for the QbloxQRM class."""
import copy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instrument_controllers.qblox.qblox_pulsar_controller import QbloxPulsarController
from qililab.instruments import QbloxQRM
from qililab.instruments.awg_settings.typings import AWGSequencerTypes, AWGTypes
from qililab.platform import Platform
from qililab.result.results import QbloxResult
from qililab.typings import InstrumentName
from qililab.typings.enums import AcquireTriggerMode, IntegrationMode, Parameter
from tests.data import Galadriel


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


@pytest.fixture(name="qrm_two_scopes")
def fixture_qrm_two_scopes():
    settings = copy.deepcopy(Galadriel.qblox_qrm_0)
    extra_sequencer = copy.deepcopy(settings[AWGTypes.AWG_SEQUENCERS.value][0])
    extra_sequencer[AWGSequencerTypes.IDENTIFIER.value] = 1
    settings[Parameter.NUM_SEQUENCERS.value] += 1
    settings[AWGTypes.AWG_SEQUENCERS.value].append(extra_sequencer)
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
            "out0_offset",
            "out1_offset",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "scope_acq_sequencer_select",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "get_acquisitions",
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
            "mixer_corr_phase_offset_degree",
            "mixer_corr_gain_ratio",
            "offset_awg_path0",
            "offset_awg_path1",
        ]
    )
    # connect to instrument
    pulsar_controller_qrm.connect()
    return pulsar_controller_qrm.modules[0]


class TestQbloxQRM:
    """Unit tests checking the QbloxQRM attributes and methods"""

    def test_inital_setup_method(self, qrm: QbloxQRM):
        """Test initial_setup method"""
        qrm.initial_setup()
        qrm.device.sequencer0.offset_awg_path0.assert_called()
        qrm.device.sequencer0.offset_awg_path1.assert_called()
        qrm.device.out0_offset.assert_called()
        qrm.device.out1_offset.assert_called()
        qrm.device.sequencer0.mixer_corr_gain_ratio.assert_called()
        qrm.device.sequencer0.mixer_corr_phase_offset_degree.assert_called()
        qrm.device.sequencer0.mod_en_awg.assert_called()
        qrm.device.sequencer0.gain_awg_path0.assert_called()
        qrm.device.sequencer0.gain_awg_path1.assert_called()
        qrm.device.scope_acq_avg_mode_en_path0.assert_called()
        qrm.device.scope_acq_avg_mode_en_path1.assert_called()
        qrm.device.scope_acq_trigger_mode_path0.assert_called()
        qrm.device.scope_acq_trigger_mode_path0.assert_called()
        qrm.device.sequencer0.mixer_corr_gain_ratio.assert_called()
        qrm.device.sequencer0.mixer_corr_phase_offset_degree.assert_called()
        qrm.device.sequencer0.sync_en.assert_called_with(qrm.awg_sequencers[0].sync_enabled)
        qrm.device.sequencer0.demod_en_acq.assert_called()
        qrm.device.sequencer0.integration_length_acq.assert_called()

    def test_double_scope_forbidden(self, qrm_two_scopes: QbloxQRM):
        """Tests that a QRM cannot have more than one sequencer storing the scope simultaneously."""
        with pytest.raises(ValueError, match="The scope can only be stored in one sequencer at a time."):
            qrm_two_scopes._obtain_scope_sequencer()

    def test_start_sequencer_method(self, qrm: QbloxQRM):
        """Test start_sequencer method"""
        qrm.start_sequencer()
        qrm.device.arm_sequencer.assert_called()
        qrm.device.start_sequencer.assert_called()

    @pytest.mark.parametrize(
        "parameter, value, channel_id",
        [
            (Parameter.GAIN, 0.02, None),
            (Parameter.GAIN_PATH0, 0.03, 0),
            (Parameter.GAIN_PATH1, 0.01, 0),
            (Parameter.OFFSET_I, 0.9, 0),
            (Parameter.OFFSET_Q, 0.12, 0),
            (Parameter.OFFSET_PATH0, 0.8, 0),
            (Parameter.OFFSET_PATH1, 0.11, 0),
            (Parameter.IF, 100_000, 0),
            (Parameter.HARDWARE_MODULATION, True, 0),
            (Parameter.HARDWARE_MODULATION, False, 0),
            (Parameter.SYNC_ENABLED, False, 0),
            (Parameter.SYNC_ENABLED, True, 0),
            (Parameter.NUM_BINS, 1, 0),
            (Parameter.GAIN_IMBALANCE, 0.1, 0),
            (Parameter.PHASE_IMBALANCE, 0.09, 0),
            (Parameter.SCOPE_ACQUIRE_TRIGGER_MODE, "sequencer", 0),
            (Parameter.SCOPE_ACQUIRE_TRIGGER_MODE, "level", 0),
            (Parameter.SCOPE_HARDWARE_AVERAGING, True, 0),
            (Parameter.SCOPE_HARDWARE_AVERAGING, False, 0),
            (Parameter.SAMPLING_RATE, 0.09, 0),
            (Parameter.HARDWARE_DEMODULATION, True, 0),
            (Parameter.HARDWARE_DEMODULATION, False, 0),
            (Parameter.INTEGRATION_LENGTH, 100, 0),
            (Parameter.INTEGRATION_MODE, "ssb", 0),
            (Parameter.SEQUENCE_TIMEOUT, 2, 0),
            (Parameter.ACQUISITION_TIMEOUT, 2, 0),
            (Parameter.ACQUISITION_DELAY_TIME, 200, None),
        ],
    )
    def test_setup_method(  # pylint: disable=too-many-branches # noqa: C901
        self,
        parameter: Parameter,
        value: float | bool | int | str,
        channel_id: int,
        qrm: QbloxQRM,
    ):
        """Test setup method"""
        qrm.setup(parameter=parameter, value=value, channel_id=channel_id)
        if channel_id is None:
            channel_id = 0
        if parameter == Parameter.GAIN:
            assert qrm.awg_sequencers[channel_id].gain_path0 == value
            assert qrm.awg_sequencers[channel_id].gain_path1 == value
        if parameter == Parameter.GAIN_PATH0:
            assert qrm.awg_sequencers[channel_id].gain_path0 == value
        if parameter == Parameter.GAIN_PATH1:
            assert qrm.awg_sequencers[channel_id].gain_path1 == value
        if parameter == Parameter.OFFSET_I:
            assert qrm.offset_i(sequencer_id=channel_id) == value
        if parameter == Parameter.OFFSET_Q:
            assert qrm.offset_q(sequencer_id=channel_id) == value
        if parameter == Parameter.OFFSET_PATH0:
            assert qrm.awg_sequencers[channel_id].offset_path0 == value
        if parameter == Parameter.OFFSET_PATH1:
            assert qrm.awg_sequencers[channel_id].offset_path1 == value
        if parameter == Parameter.IF:
            assert qrm.awg_sequencers[channel_id].intermediate_frequency == value
        if parameter == Parameter.HARDWARE_MODULATION:
            assert qrm.awg_sequencers[channel_id].hardware_modulation == value
        if parameter == Parameter.SYNC_ENABLED:
            assert qrm.awg_sequencers[channel_id].sync_enabled == value
        if parameter == Parameter.NUM_BINS:
            assert qrm.awg_sequencers[channel_id].num_bins == value
        if parameter == Parameter.GAIN_IMBALANCE:
            assert qrm.awg_sequencers[channel_id].gain_imbalance == value
        if parameter == Parameter.PHASE_IMBALANCE:
            assert qrm.awg_sequencers[channel_id].phase_imbalance == value
        if parameter == Parameter.SCOPE_HARDWARE_AVERAGING:
            assert qrm.awg_sequencers[channel_id].scope_hardware_averaging == value
        if parameter == Parameter.HARDWARE_DEMODULATION:
            assert qrm.awg_sequencers[channel_id].hardware_demodulation == value
        if parameter == Parameter.SCOPE_ACQUIRE_TRIGGER_MODE:
            assert qrm.awg_sequencers[channel_id].scope_acquire_trigger_mode == AcquireTriggerMode(value)
        if parameter == Parameter.INTEGRATION_LENGTH:
            assert qrm.awg_sequencers[channel_id].integration_length == value
        if parameter == Parameter.SAMPLING_RATE:
            assert qrm.awg_sequencers[channel_id].sampling_rate == value
        if parameter == Parameter.INTEGRATION_MODE:
            assert qrm.awg_sequencers[channel_id].integration_mode == IntegrationMode(value)
        if parameter == Parameter.SEQUENCE_TIMEOUT:
            assert qrm.awg_sequencers[channel_id].sequence_timeout == value
        if parameter == Parameter.ACQUISITION_TIMEOUT:
            assert qrm.awg_sequencers[channel_id].acquisition_timeout == value
        if parameter == Parameter.ACQUISITION_DELAY_TIME:
            assert qrm.acquisition_delay_time == value

    def test_setup_raises_error(self, qrm: QbloxQRM):
        """Test that the ``setup`` method raises an error when called with a channel id bigger than the number of
        sequencers."""
        with pytest.raises(ValueError, match="the specified channel id:9 is out of range. Number of sequencers is 1"):
            qrm.setup(parameter=Parameter.GAIN, value=1, channel_id=9)

    def test_turn_off_method(self, qrm: QbloxQRM):
        """Test turn_off method"""
        qrm.turn_off()
        qrm.device.stop_sequencer.assert_called()

    def test_reset_method(self, qrm: QbloxQRM):
        """Test reset method"""
        qrm._cache = {0: None}  # type: ignore # pylint: disable=protected-access
        qrm.reset()
        assert qrm._cache == {}  # pylint: disable=protected-access

    def test_compile(self, qrm, pulse_bus_schedule):
        """Test compile method."""
        pulse_bus_schedule.port = 1  # change port to target the resonator
        sequences = qrm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=2000)
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)

    def test_acquisition_data_is_removed_when_calling_compile_twice(self, qrm, pulse_bus_schedule):
        """Test that the acquisition data of the QRM device is deleted when calling compile twice."""
        pulse_bus_schedule.port = 1  # change port to target the resonator
        sequences = qrm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=100)
        qrm.upload()
        sequences2 = qrm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=100)
        assert len(sequences) == 1
        assert len(sequences2) == 1
        assert sequences[0] is sequences2[0]
        qrm.device.delete_acquisition_data.assert_called_once()

    def test_upload_raises_error(self, qrm):
        """Test upload method raises error."""
        with pytest.raises(ValueError, match="Please compile the circuit before uploading it to the device"):
            qrm.upload()

    def test_upload_method(self, qrm, pulse_bus_schedule):
        """Test upload method"""
        qrm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=100)
        qrm.upload()
        qrm.device.sequencer0.sequence.assert_called_once()

    def test_get_acquisitions_method(self, qrm: QbloxQRM):
        """Test get_acquisitions_method"""
        qrm.device.get_acquisitions.return_value = {
            "default": {
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
        acquisitions = qrm.get_acquisitions()
        assert isinstance(acquisitions, QbloxResult)
        # Assert device calls
        qrm.device.get_sequencer_state.assert_called()
        qrm.device.get_acquisition_state.assert_called()
        qrm.device.get_acquisitions.assert_called()

    def test_id_property(self, qrm_no_device: QbloxQRM):
        """Test id property."""
        assert qrm_no_device.id_ == qrm_no_device.settings.id_

    def test_name_property(self, qrm_no_device: QbloxQRM):
        """Test name property."""
        assert qrm_no_device.name == InstrumentName.QBLOX_QRM

    def test_category_property(self, qrm_no_device: QbloxQRM):
        """Test category property."""
        assert qrm_no_device.category == qrm_no_device.settings.category

    def test_integration_length_property(self, qrm_no_device: QbloxQRM):
        """Test integration_length property."""
        assert qrm_no_device.integration_length(0) == qrm_no_device.awg_sequencers[0].integration_length

    def tests_firmware_property(self, qrm_no_device: QbloxQRM):
        """Test firmware property."""
        assert qrm_no_device.firmware == qrm_no_device.settings.firmware
