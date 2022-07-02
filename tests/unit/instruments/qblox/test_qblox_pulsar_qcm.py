"""Tests for the QbloxQCM class."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments import QbloxQCM
from qililab.typings import InstrumentName


class TestQbloxQCM:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_inital_setup_method(self, qcm: QbloxQCM):
        """Test initial_setup method"""
        qcm.initial_setup()
        qcm.device.reference_source.assert_called_with(qcm.reference_clock.value)
        qcm.device.sequencer0.sync_en.assert_called_with(qcm.sync_enabled)

    def test_start_sequencer_method(self, qcm: QbloxQCM):
        """Test start_sequencer method"""
        qcm.start_sequencer()
        qcm.device.arm_sequencer.assert_called()
        qcm.device.start_sequencer.assert_called()

    def test_setup_method(self, qcm: QbloxQCM):
        """Test setup method"""
        qcm.setup()
        qcm.device.sequencer0.gain_awg_path0.assert_called_once_with(qcm.gain)
        qcm.device.sequencer0.gain_awg_path1.assert_called_once_with(qcm.gain)
        qcm.device.sequencer0.offset_awg_path0.assert_called_once_with(qcm.offset_i)
        qcm.device.sequencer0.offset_awg_path1.assert_called_once_with(qcm.offset_q)

    def test_stop_method(self, qcm: QbloxQCM):
        """Test stop method"""
        qcm.stop()
        qcm.device.stop_sequencer.assert_called_once()

    @patch("qililab.instruments.qblox.qblox_pulsar.json.dump", return_value=None)
    def test_upload_method(self, mock_dump: MagicMock, qcm: QbloxQCM):
        """Test upload method"""
        qcm.upload(
            sequence=Sequence(program={}, waveforms=Waveforms(), acquisitions=Acquisitions(), weights={}),
            path=Path(__file__).parent,
        )
        qcm.device.sequencer0.sequence.assert_called_once()
        mock_dump.assert_called_once()

    def test_id_property(self, qcm: QbloxQCM):
        """Test id property."""
        assert qcm.id_ == qcm.settings.id_

    def test_name_property(self, qcm: QbloxQCM):
        """Test name property."""
        assert qcm.name == InstrumentName.QBLOX_QCM

    def test_category_property(self, qcm: QbloxQCM):
        """Test category property."""
        assert qcm.category == qcm.settings.category

    def test_firmware_property(self, qcm: QbloxQCM):
        """Test firmware property."""
        assert qcm.firmware == qcm.settings.firmware

    def test_frequency_property(self, qcm: QbloxQCM):
        """Test frequency property."""
        assert qcm.frequency == qcm.settings.frequency
