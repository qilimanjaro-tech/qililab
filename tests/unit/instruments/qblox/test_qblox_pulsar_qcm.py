"""Tests for the QbloxQCM class."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments import QbloxQCM
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter


class TestQbloxQCM:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_inital_setup_method(self, qcm: QbloxQCM):
        """Test initial_setup method"""
        qcm.initial_setup()
        qcm.device.sequencer0.sync_en.assert_called_with(qcm.sync_enabled[0])
        qcm.device.sequencer0.mod_en_awg.assert_called()
        qcm.device.sequencer0.offset_awg_path0.assert_called()
        qcm.device.sequencer0.offset_awg_path1.assert_called()
        qcm.device.sequencer0.mixer_corr_gain_ratio.assert_called()
        qcm.device.sequencer0.mixer_corr_phase_offset_degree.assert_called()

    def test_start_sequencer_method(self, qcm: QbloxQCM):
        """Test start_sequencer method"""
        qcm.start_sequencer()
        qcm.device.arm_sequencer.assert_called()
        qcm.device.start_sequencer.assert_called()

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
        ],
    )
    def test_setup_method(self, parameter: Parameter, value: float | bool | int, channel_id: int, qcm: QbloxQCM):
        """Test setup method"""
        qcm.setup(parameter=parameter, value=value, channel_id=channel_id)
        if parameter == Parameter.GAIN:
            assert qcm.settings.gain[channel_id] == value
        if parameter == Parameter.OFFSET_I:
            assert qcm.settings.offset_i[channel_id] == value
        if parameter == Parameter.OFFSET_Q:
            assert qcm.settings.offset_q[channel_id] == value
        if parameter == Parameter.IF:
            assert qcm.settings.intermediate_frequencies[channel_id] == value
        if parameter == Parameter.HARDWARE_MODULATION:
            assert qcm.settings.hardware_modulation[channel_id] == value
        if parameter == Parameter.SYNC_ENABLED:
            assert qcm.settings.sync_enabled[channel_id] == value
        if parameter == Parameter.NUM_BINS:
            assert qcm.settings.num_bins[channel_id] == value
        if parameter == Parameter.GAIN_IMBALANCE:
            assert qcm.settings.gain_imbalance[channel_id] == value
        if parameter == Parameter.PHASE_IMBALANCE:
            assert qcm.settings.phase_imbalance[channel_id] == value

    def test_turn_off_method(self, qcm: QbloxQCM):
        """Test turn_off method"""
        qcm.turn_off()
        qcm.device.stop_sequencer.assert_called_once()

    def test_reset_method(self, qrm: QbloxQCM):
        """Test reset method"""
        qrm._cache = [None, 0, 0]  # type: ignore # pylint: disable=protected-access
        qrm.reset()
        assert qrm._cache is None  # pylint: disable=protected-access

    @patch("qililab.instruments.qblox.qblox_module.json.dump", return_value=None)
    def test_upload_method(self, mock_dump: MagicMock, qcm: QbloxQCM):
        """Test upload method"""
        qcm.upload(
            sequence=Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights={}),
            path=Path(__file__).parent,
        )
        qcm.device.sequencer0.sequence.assert_called_once()
        mock_dump.assert_called_once()

    def test_id_property(self, qcm_no_device: QbloxQCM):
        """Test id property."""
        assert qcm_no_device.id_ == qcm_no_device.settings.id_

    def test_name_property(self, qcm_no_device: QbloxQCM):
        """Test name property."""
        assert qcm_no_device.name == InstrumentName.QBLOX_QCM

    def test_category_property(self, qcm_no_device: QbloxQCM):
        """Test category property."""
        assert qcm_no_device.category == qcm_no_device.settings.category

    def test_firmware_property(self, qcm_no_device: QbloxQCM):
        """Test firmware property."""
        assert qcm_no_device.firmware == qcm_no_device.settings.firmware

    def test_frequency_property(self, qcm_no_device: QbloxQCM):
        """Test frequency property."""
        assert qcm_no_device.frequency == qcm_no_device.intermediate_frequencies[0]
