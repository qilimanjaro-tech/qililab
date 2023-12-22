"""Test for the QbloxQRM class."""
import copy
import re
from unittest.mock import MagicMock, Mock, patch

import pytest

from qililab.instrument_controllers.qblox.qblox_pulsar_controller import QbloxPulsarController
from qililab.instruments import ParameterNotFound
from qililab.instruments.awg_settings.awg_qblox_adc_sequencer import AWGQbloxADCSequencer
from qililab.instruments.awg_settings.typings import AWGSequencerTypes, AWGTypes
from qililab.instruments.qblox import QbloxQRM
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.result.qblox_results import QbloxResult
from qililab.typings import InstrumentName
from qililab.typings.enums import AcquireTriggerMode, IntegrationMode, Parameter
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="settings_6_sequencers")
def fixture_settings_6_sequencers():
    """6 sequencers fixture"""
    sequencers = [
        {
            "identifier": seq_idx,
            "chip_port_id": "feedline_input",
            "qubit": 5 - seq_idx,
            "output_i": 1,
            "output_q": 0,
            "weights_i": [1, 1, 1, 1],
            "weights_q": [1, 1, 1, 1],
            "weighed_acq_enabled": False,
            "threshold": 0.5,
            "threshold_rotation": 30.0 * seq_idx,
            "num_bins": 1,
            "intermediate_frequency": 20000000,
            "gain_i": 0.001,
            "gain_q": 0.02,
            "gain_imbalance": 1,
            "phase_imbalance": 0,
            "offset_i": 0,
            "offset_q": 0,
            "hardware_modulation": True,
            "scope_acquire_trigger_mode": "sequencer",
            "scope_hardware_averaging": True,
            "sampling_rate": 1000000000,
            "integration_length": 8000,
            "integration_mode": "ssb",
            "sequence_timeout": 1,
            "acquisition_timeout": 1,
            "hardware_demodulation": True,
            "scope_store_enabled": True,
        }
        for seq_idx in range(6)
    ]
    return {
        "alias": "test",
        "firmware": "0.4.0",
        "num_sequencers": 6,
        "out_offsets": [0.123, 1.23],
        "acquisition_delay_time": 100,
        "awg_sequencers": sequencers,
    }


@pytest.fixture(name="settings_even_sequencers")
def fixture_settings_even_sequencers():
    """module with even sequencers"""
    sequencers = [
        {
            "identifier": seq_idx,
            "chip_port_id": "feedline_input",
            "qubit": 5 - seq_idx,
            "output_i": 1,
            "output_q": 0,
            "weights_i": [1, 1, 1, 1],
            "weights_q": [1, 1, 1, 1],
            "weighed_acq_enabled": False,
            "threshold": 0.5,
            "threshold_rotation": 30.0 * seq_idx,
            "num_bins": 1,
            "intermediate_frequency": 20000000,
            "gain_i": 0.001,
            "gain_q": 0.02,
            "gain_imbalance": 1,
            "phase_imbalance": 0,
            "offset_i": 0,
            "offset_q": 0,
            "hardware_modulation": True,
            "scope_acquire_trigger_mode": "sequencer",
            "scope_hardware_averaging": True,
            "sampling_rate": 1000000000,
            "integration_length": 8000,
            "integration_mode": "ssb",
            "sequence_timeout": 1,
            "acquisition_timeout": 1,
            "hardware_demodulation": True,
            "scope_store_enabled": True,
        }
        for seq_idx in range(0, 6, 2)
    ]
    return {
        "alias": "test",
        "firmware": "0.4.0",
        "num_sequencers": 3,
        "out_offsets": [0.123, 1.23],
        "acquisition_delay_time": 100,
        "awg_sequencers": sequencers,
    }


@pytest.fixture(name="local_cfg_qrm")
def fixture_local_cfg_qrm(settings_6_sequencers: dict) -> QbloxQRM:
    """qblox module fixture

    Args:
        settings_6_sequencers (dict): qrm with 6 sequencers settings

    Returns:
        QbloxQRM: QRM object
    """
    return QbloxQRM(settings=settings_6_sequencers)


@pytest.fixture(name="pulsar_controller_qrm")
def fixture_pulsar_controller_qrm():
    """Return an instance of QbloxPulsarController class"""
    platform = build_platform(runcard=Galadriel.runcard)
    settings = copy.deepcopy(Galadriel.pulsar_controller_qrm_0)
    settings.pop("name")
    return QbloxPulsarController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="qrm_no_device")
def fixture_qrm_no_device() -> QbloxQRM:
    """Return an instance of QbloxQRM class"""
    settings = copy.deepcopy(Galadriel.qblox_qrm_0)
    settings.pop("name")
    return QbloxQRM(settings=settings)


@pytest.fixture(name="qrm_two_scopes")
def fixture_qrm_two_scopes():
    """qrm fixture"""
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
            "sequencer1",
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
    mock_instance.sequencers = [mock_instance.sequencer0, mock_instance.sequencer1]
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
            "thresholded_acq_threshold",
            "thresholded_acq_rotation",
            "marker_ovr_en",
            "marker_ovr_value",
        ]
    )
    # connect to instrument
    pulsar_controller_qrm.connect()
    return pulsar_controller_qrm.modules[0]


class TestQbloxQRM:
    """Unit tests checking the QbloxQRM attributes and methods"""

    def test_error_post_init_too_many_seqs(self, settings_6_sequencers: dict):
        """test that init raises an error if there are too many sequencers"""
        num_sequencers = 7
        settings_6_sequencers["num_sequencers"] = num_sequencers
        error_string = re.escape(
            "The number of sequencers must be greater than 0 and less or equal than "
            + f"{QbloxModule._NUM_MAX_SEQUENCERS}. Received: {num_sequencers}"  # pylint: disable=protected-access
        )

        with pytest.raises(ValueError, match=error_string):
            QbloxQRM(settings_6_sequencers)

    def test_error_post_init_0_seqs(self, settings_6_sequencers: dict):
        """test that errror is raised in no sequencers are found"""
        num_sequencers = 0
        settings_6_sequencers["num_sequencers"] = num_sequencers
        error_string = re.escape(
            "The number of sequencers must be greater than 0 and less or equal than "
            + f"{QbloxModule._NUM_MAX_SEQUENCERS}. Received: {num_sequencers}"  # pylint: disable=protected-access
        )

        with pytest.raises(ValueError, match=error_string):
            QbloxQRM(settings_6_sequencers)

    def test_error_awg_seqs_neq_seqs(self, settings_6_sequencers: dict):
        """test taht error is raised if awg sequencers in settings and those in device dont match"""
        num_sequencers = 5
        settings_6_sequencers["num_sequencers"] = num_sequencers
        error_string = re.escape(
            f"The number of sequencers: {num_sequencers} does not match"
            + f" the number of AWG Sequencers settings specified: {len(settings_6_sequencers['awg_sequencers'])}"
        )
        with pytest.raises(ValueError, match=error_string):
            QbloxQRM(settings_6_sequencers)

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
        qrm.device.sequencers[0].mixer_corr_gain_ratio.assert_called()
        qrm.device.sequencers[0].mixer_corr_phase_offset_degree.assert_called()
        qrm.device.sequencers[0].sync_en.assert_called_with(False)
        qrm.device.sequencers[0].demod_en_acq.assert_called()
        qrm.device.sequencers[0].integration_length_acq.assert_called()
        qrm.device.sequencers[0].thresholded_acq_threshold.assert_called()
        qrm.device.sequencers[0].thresholded_acq_rotation.assert_called()

    def test_double_scope_forbidden(self, qrm_two_scopes: QbloxQRM):
        """Tests that a QRM cannot have more than one sequencer storing the scope simultaneously."""
        with pytest.raises(ValueError, match="The scope can only be stored in one sequencer at a time."):
            qrm_two_scopes._obtain_scope_sequencer()  # pylint: disable=protected-access

    @pytest.mark.parametrize(
        "parameter, value, channel_id",
        [
            (Parameter.GAIN, 0.02, 0),
            (Parameter.GAIN_I, 0.03, 0),
            (Parameter.GAIN_Q, 0.01, 0),
            (Parameter.OFFSET_I, 0.8, 0),
            (Parameter.OFFSET_Q, 0.11, 0),
            (Parameter.OFFSET_OUT0, 1.234, 0),
            (Parameter.OFFSET_OUT1, 0, 0),
            (Parameter.IF, 100_000, 0),
            (Parameter.HARDWARE_MODULATION, True, 0),
            (Parameter.HARDWARE_MODULATION, False, 0),
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
            (Parameter.ACQUISITION_DELAY_TIME, 200, 0),
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
            assert qrm.awg_sequencers[channel_id].gain_i == value
            assert qrm.awg_sequencers[channel_id].gain_q == value
        if parameter == Parameter.GAIN_I:
            assert qrm.awg_sequencers[channel_id].gain_i == value
        if parameter == Parameter.GAIN_Q:
            assert qrm.awg_sequencers[channel_id].gain_q == value
        if parameter == Parameter.OFFSET_I:
            assert qrm.awg_sequencers[channel_id].offset_i == value
        if parameter == Parameter.OFFSET_Q:
            assert qrm.awg_sequencers[channel_id].offset_q == value
        if parameter == Parameter.IF:
            assert qrm.awg_sequencers[channel_id].intermediate_frequency == value
        if parameter == Parameter.HARDWARE_MODULATION:
            assert qrm.awg_sequencers[channel_id].hardware_modulation == value
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
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            assert qrm.out_offsets[output] == value

    def test_setup_raises_error(self, qrm: QbloxQRM):
        """Test that the ``setup`` method raises an error when called with a channel id bigger than the number of
        sequencers."""
        with pytest.raises(
            ParameterNotFound, match="the specified channel id:9 is out of range. Number of sequencers is 2"
        ):
            qrm.setup(parameter=Parameter.GAIN, value=1, channel_id=9)

    def test_setup_out_offset_raises_error(self, qrm: QbloxQRM):
        """Test that calling ``_set_out_offset`` with a wrong output value raises an error."""
        with pytest.raises(IndexError, match="Output 5 is out of range"):
            qrm._set_out_offset(output=5, value=1)  # pylint: disable=protected-access

    def test_turn_off_method(self, qrm: QbloxQRM):
        """Test turn_off method"""
        qrm.turn_off()
        qrm.device.stop_sequencer.assert_called()

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
        qrm.device.get_sequencer_state.assert_not_called()
        qrm.device.get_acquisition_state.assert_not_called()
        qrm.device.get_acquisitions.assert_not_called()

    def test_get_qprogram_acquisitions_method(self, qrm: QbloxQRM):
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
        qrm.sequences = {0: None, 1: None}
        acquisitions = qrm.acquire_qprogram_results(acquisitions=["default"])
        assert isinstance(acquisitions, list)
        assert len(acquisitions) == 2

    def test_name_property(self, qrm_no_device: QbloxQRM):
        """Test name property."""
        assert qrm_no_device.name == InstrumentName.QBLOX_QRM

    def test_integration_length_property(self, qrm_no_device: QbloxQRM):
        """Test integration_length property."""
        assert qrm_no_device.integration_length(0) == qrm_no_device.awg_sequencers[0].integration_length

    def tests_firmware_property(self, qrm_no_device: QbloxQRM):
        """Test firmware property."""
        assert qrm_no_device.firmware == qrm_no_device.settings.firmware

    def test_getting_even_sequencers(self, settings_even_sequencers: dict):
        """Tests the method QbloxQRM._get_sequencers_by_id() for a QbloxQRM with only the even sequencers configured."""
        qrm = QbloxQRM(settings=settings_even_sequencers)
        for seq_id in range(6):
            if seq_id % 2 == 0:
                assert qrm._get_sequencer_by_id(id=seq_id).identifier == seq_id  # pylint: disable=protected-access
            else:
                with pytest.raises(IndexError, match=f"There is no sequencer with id={seq_id}."):
                    qrm._get_sequencer_by_id(id=seq_id)  # pylint: disable=protected-access


class TestAWGQbloxADCSequencer:  # pylint: disable=too-few-public-methods
    """Unit tests for AWGQbloxADCSequencer class."""

    def test_verify_weights(self):
        """Test the _verify_weights method."""
        mock_sequencer = Mock(spec=AWGQbloxADCSequencer)
        mock_sequencer.weights_i = [1.0]
        mock_sequencer.weights_q = [1.0, 1.0]

        with pytest.raises(IndexError, match="The length of weights_i and weights_q must be equal."):
            AWGQbloxADCSequencer._verify_weights(mock_sequencer)  # pylint: disable=protected-access
