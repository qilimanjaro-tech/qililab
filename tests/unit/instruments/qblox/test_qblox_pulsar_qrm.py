"""Test for the QbloxQRM class."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments import QbloxQRM
from qililab.result.results import QbloxResult
from qililab.typings import InstrumentName
from qililab.typings.enums import AcquireTriggerMode, IntegrationMode, Parameter


class TestQbloxQRM:
    """Unit tests checking the QbloxQRM attributes and methods"""

    def test_inital_setup_method(self, qrm: QbloxQRM):
        """Test initial_setup method"""
        qrm.initial_setup()
        qrm.device.sequencer0.offset_awg_path0.assert_called()
        qrm.device.sequencer0.offset_awg_path1.assert_called()
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
        qrm.device.sequencer0.sync_en.assert_called_with(qrm.sync_enabled[0])
        qrm.device.sequencer0.demod_en_acq.assert_called()
        qrm.device.sequencer0.integration_length_acq.assert_called()

    def test_start_sequencer_method(self, qrm: QbloxQRM):
        """Test start_sequencer method"""
        qrm.start_sequencer()
        qrm.device.arm_sequencer.assert_called()
        qrm.device.start_sequencer.assert_called()

    @pytest.mark.parametrize(
        "parameter, value, channel_id",
        [
            (Parameter.GAIN, 0.01, 0),
            (Parameter.OFFSET_I, 0.1, 0),
            (Parameter.OFFSET_Q, 0.1, 0),
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
        if parameter == Parameter.GAIN:
            assert qrm.settings.gain[channel_id] == value
        if parameter == Parameter.OFFSET_I:
            assert qrm.settings.offset_i[channel_id] == value
        if parameter == Parameter.OFFSET_Q:
            assert qrm.settings.offset_q[channel_id] == value
        if parameter == Parameter.IF:
            assert qrm.settings.intermediate_frequencies[channel_id] == value
        if parameter == Parameter.HARDWARE_MODULATION:
            assert qrm.settings.hardware_modulation[channel_id] == value
        if parameter == Parameter.SYNC_ENABLED:
            assert qrm.settings.sync_enabled[channel_id] == value
        if parameter == Parameter.NUM_BINS:
            assert qrm.settings.num_bins[channel_id] == value
        if parameter == Parameter.GAIN_IMBALANCE:
            assert qrm.settings.gain_imbalance[channel_id] == value
        if parameter == Parameter.PHASE_IMBALANCE:
            assert qrm.settings.phase_imbalance[channel_id] == value
        if parameter == Parameter.SCOPE_HARDWARE_AVERAGING:
            assert qrm.settings.scope_hardware_averaging[channel_id] == value
        if parameter == Parameter.HARDWARE_DEMODULATION:
            assert qrm.settings.hardware_demodulation[channel_id] == value
        if parameter == Parameter.SCOPE_ACQUIRE_TRIGGER_MODE:
            assert qrm.settings.scope_acquire_trigger_mode[channel_id] == AcquireTriggerMode(value)
        if parameter == Parameter.INTEGRATION_LENGTH:
            assert qrm.settings.integration_length[channel_id] == value
        if parameter == Parameter.SAMPLING_RATE:
            assert qrm.settings.sampling_rate[channel_id] == value
        if parameter == Parameter.INTEGRATION_MODE:
            assert qrm.settings.integration_mode[channel_id] == IntegrationMode(value)
        if parameter == Parameter.SEQUENCE_TIMEOUT:
            assert qrm.settings.sequence_timeout[channel_id] == value
        if parameter == Parameter.ACQUISITION_TIMEOUT:
            assert qrm.settings.acquisition_timeout[channel_id] == value
        if parameter == Parameter.ACQUISITION_DELAY_TIME:
            assert qrm.settings.acquisition_delay_time == value

    def test_turn_off_method(self, qrm: QbloxQRM):
        """Test turn_off method"""
        qrm.turn_off()
        qrm.device.stop_sequencer.assert_called()

    def test_reset_method(self, qrm: QbloxQRM):
        """Test reset method"""
        qrm._cache = [None, 0, 0]  # type: ignore # pylint: disable=protected-access
        qrm.reset()
        assert qrm._cache is None  # pylint: disable=protected-access

    @patch("qililab.instruments.qblox.qblox_module.json.dump", return_value=None)
    def test_upload_method(self, mock_dump: MagicMock, qrm: QbloxQRM):
        """Test upload method"""
        qrm.upload(
            sequence=Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights={}),
            path=Path(__file__).parent,
        )
        qrm.device.sequencer0.sequence.assert_called()
        mock_dump.assert_called_once()

    def test_get_acquisitions_method(self, qrm: QbloxQRM):
        """Test get_acquisitions_method"""
        qrm.device.get_acquisitions.return_value = {
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

    def test_acquire_trigger_mode_property(self, qrm_no_device: QbloxQRM):
        """Test scope_acquire_trigger_mode property."""
        assert qrm_no_device.scope_acquire_trigger_mode == qrm_no_device.settings.scope_acquire_trigger_mode

    def test_hardware_averaging_property(self, qrm_no_device: QbloxQRM):
        """Test hardware_averaging property."""
        assert qrm_no_device.scope_hardware_averaging == qrm_no_device.settings.scope_hardware_averaging

    def test_scope_store_enabled(self, qrm_no_device: QbloxQRM):
        """Test scope_store_enabled property."""
        assert qrm_no_device.scope_store_enabled == qrm_no_device.settings.scope_store_enabled

    def test_sampling_rate_property(self, qrm_no_device: QbloxQRM):
        """Test sampling_rate property."""
        assert qrm_no_device.sampling_rate == qrm_no_device.settings.sampling_rate

    def test_integration_length_property(self, qrm_no_device: QbloxQRM):
        """Test integration_length property."""
        assert qrm_no_device.integration_length == qrm_no_device.settings.integration_length

    def test_integration_mode_property(self, qrm_no_device: QbloxQRM):
        """Test integration_mode property."""
        assert qrm_no_device.integration_mode == qrm_no_device.settings.integration_mode

    def test_sequence_timeout_property(self, qrm_no_device: QbloxQRM):
        """Test sequence_timeout property."""
        assert qrm_no_device.sequence_timeout == qrm_no_device.settings.sequence_timeout

    def test_acquisition_timeout_property(self, qrm_no_device: QbloxQRM):
        """Test acquisition_timeout property."""
        assert qrm_no_device.acquisition_timeout == qrm_no_device.settings.acquisition_timeout

    def test_acquisition_name_method(self, qrm_no_device: QbloxQRM):
        """Test acquisition_name method."""
        assert isinstance(qrm_no_device.acquisition_name(sequencer=0), str)

    def tests_delay_time_property(self, qrm_no_device: QbloxQRM):
        """Test acquisition_delay_time property."""
        assert qrm_no_device.acquisition_delay_time == qrm_no_device.settings.acquisition_delay_time

    def tests_firmware_property(self, qrm_no_device: QbloxQRM):
        """Test firmware property."""
        assert qrm_no_device.firmware == qrm_no_device.settings.firmware

    def tests_frequency_property(self, qrm_no_device: QbloxQRM):
        """Test frequency property."""
        assert qrm_no_device.frequency == qrm_no_device.settings.intermediate_frequencies[0]

    def tests_gain_imbalance_property(self, qrm_no_device: QbloxQRM):
        """Test gain_imbalance property."""
        assert qrm_no_device.gain_imbalance == qrm_no_device.settings.gain_imbalance

    def tests_phase_imbalance_property(self, qrm_no_device: QbloxQRM):
        """Test phase_imbalance property."""
        assert qrm_no_device.phase_imbalance == qrm_no_device.settings.phase_imbalance

    def tests_offset_i_property(self, qrm_no_device: QbloxQRM):
        """Test offset_i property."""
        assert qrm_no_device.offset_i == qrm_no_device.settings.offset_i

    def tests_offset_q_property(self, qrm_no_device: QbloxQRM):
        """Test offset_q property."""
        assert qrm_no_device.offset_q == qrm_no_device.settings.offset_q
