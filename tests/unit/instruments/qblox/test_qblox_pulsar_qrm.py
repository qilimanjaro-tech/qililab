"""Test for the QbloxQRM class."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from qpysequence.acquisitions import Acquisitions
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments import QbloxQRM
from qililab.result import QbloxResult
from qililab.typings import InstrumentName


class TestQbloxQRM:
    """Unit tests checking the QbloxQRM attributes and methods"""

    def test_inital_setup_method(self, qrm: QbloxQRM):
        """Test initial_setup method"""
        qrm.initial_setup()
        qrm.device.reference_source.assert_called_with(qrm.reference_clock.value)
        qrm.device.sequencer0.sync_en.assert_called_with(qrm.sync_enabled)

    def test_start_sequencer_method(self, qrm: QbloxQRM):
        """Test start_sequencer method"""
        qrm.start_sequencer()
        qrm.device.arm_sequencer.assert_called()
        qrm.device.start_sequencer.assert_called()

    def test_setup_method(self, qrm: QbloxQRM):
        """Test setup method"""
        qrm.setup()
        qrm.device.sequencer0.gain_awg_path0.assert_called()
        qrm.device.sequencer0.gain_awg_path1.assert_called()
        qrm.device.scope_acq_avg_mode_en_path0.assert_called()
        qrm.device.scope_acq_avg_mode_en_path1.assert_called()
        qrm.device.scope_acq_trigger_mode_path0.assert_called()
        qrm.device.scope_acq_trigger_mode_path0.assert_called()
        qrm.device.sequencer0.offset_awg_path0.assert_called()
        qrm.device.sequencer0.offset_awg_path1.assert_called()

    def test_stop_method(self, qrm: QbloxQRM):
        """Test stop method"""
        qrm.stop()
        qrm.device.stop_sequencer.assert_called_once()

    @patch("qililab.instruments.qblox.qblox_pulsar.json.dump", return_value=None)
    def test_upload_method(self, mock_dump: MagicMock, qrm: QbloxQRM):
        """Test upload method"""
        qrm.upload(
            sequence=Sequence(program={}, waveforms=Waveforms(), acquisitions=Acquisitions(), weights={}),
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

    def test_id_property(self, qrm: QbloxQRM):
        """Test id property."""
        assert qrm.id_ == qrm.settings.id_

    def test_name_property(self, qrm: QbloxQRM):
        """Test name property."""
        assert qrm.name == InstrumentName.QBLOX_QRM

    def test_category_property(self, qrm: QbloxQRM):
        """Test category property."""
        assert qrm.category == qrm.settings.category

    def test_acquire_trigger_mode_property(self, qrm: QbloxQRM):
        """Test scope_acquire_trigger_mode property."""
        assert qrm.scope_acquire_trigger_mode == qrm.settings.scope_acquire_trigger_mode

    def test_hardware_averaging_property(self, qrm: QbloxQRM):
        """Test hardware_averaging property."""
        assert qrm.scope_hardware_averaging == qrm.settings.scope_hardware_averaging

    def test_sampling_rate_property(self, qrm: QbloxQRM):
        """Test sampling_rate property."""
        assert qrm.sampling_rate == qrm.settings.sampling_rate

    def test_integration_length_property(self, qrm: QbloxQRM):
        """Test integration_length property."""
        assert qrm.integration_length == qrm.settings.integration_length

    def test_integration_mode_property(self, qrm: QbloxQRM):
        """Test integration_mode property."""
        assert qrm.integration_mode == qrm.settings.integration_mode

    def test_sequence_timeout_property(self, qrm: QbloxQRM):
        """Test sequence_timeout property."""
        assert qrm.sequence_timeout == qrm.settings.sequence_timeout

    def test_acquisition_timeout_property(self, qrm: QbloxQRM):
        """Test acquisition_timeout property."""
        assert qrm.acquisition_timeout == qrm.settings.acquisition_timeout

    def test_acquisition_name_property(self, qrm: QbloxQRM):
        """Test acquisition_name property."""
        assert isinstance(qrm.acquisition_name, str)

    def tests_delay_time_property(self, qrm: QbloxQRM):
        """Test acquisition_delay_time property."""
        assert qrm.acquisition_delay_time == qrm.settings.acquisition_delay_time

    def tests_firmware_property(self, qrm: QbloxQRM):
        """Test firmware property."""
        assert qrm.firmware == qrm.settings.firmware

    def tests_frequency_property(self, qrm: QbloxQRM):
        """Test frequency property."""
        assert qrm.frequency == qrm.settings.frequency

    def tests_epsilon_property(self, qrm: QbloxQRM):
        """Test epsilon property."""
        assert qrm.epsilon == qrm.settings.epsilon

    def tests_delta_property(self, qrm: QbloxQRM):
        """Test delta property."""
        assert qrm.delta == qrm.settings.delta

    def tests_offset_i_property(self, qrm: QbloxQRM):
        """Test offset_i property."""
        assert qrm.offset_i == qrm.settings.offset_i

    def tests_offset_q_property(self, qrm: QbloxQRM):
        """Test offset_q property."""
        assert qrm.offset_q == qrm.settings.offset_q
