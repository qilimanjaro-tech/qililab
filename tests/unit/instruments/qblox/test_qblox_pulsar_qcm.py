"""Tests for the QbloxPulsarQCM class."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments import QbloxPulsarQCM
from qililab.typings import InstrumentName


class TestQbloxPulsarQCM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_connect_method_raises_error(self, qcm: QbloxPulsarQCM):
        """Test that calling again connect raises a ValueError"""
        with pytest.raises(ValueError):
            qcm.connect()

    def test_inital_setup_method(self, qcm: QbloxPulsarQCM):
        """Test initial_setup method"""
        qcm.initial_setup()
        qcm.device.reference_source.assert_called_with(qcm.reference_clock.value)
        qcm.device.sequencer0.sync_en.assert_called_with(qcm.sync_enabled)

    def test_start_sequencer_method(self, qcm: QbloxPulsarQCM):
        """Test start_sequencer method"""
        qcm.start_sequencer()
        qcm.device.arm_sequencer.assert_called()
        qcm.device.start_sequencer.assert_called()

    def test_setup_method(self, qcm: QbloxPulsarQCM):
        """Test setup method"""
        qcm.setup()
        qcm.device.sequencer0.gain_awg_path0.assert_called()
        qcm.device.sequencer0.gain_awg_path1.assert_called()
        qcm.device.sequencer0.offset_awg_path0.assert_called()
        qcm.device.sequencer0.offset_awg_path1.assert_called()

    def test_stop_method(self, qcm: QbloxPulsarQCM):
        """Test stop method"""
        qcm.stop()
        qcm.device.stop_sequencer.assert_called_once()

    def test_reset_method(self, qcm: QbloxPulsarQCM):
        """Test reset method"""
        qcm.reset()
        qcm.device.reset.assert_called()

    @patch("qililab.instruments.qblox.qblox_pulsar.json.dump", return_value=None)
    def test_upload_method(self, mock_dump: MagicMock, qcm: QbloxPulsarQCM):
        """Test upload method"""
        qcm.upload(
            sequence=Sequence(program={}, waveforms=Waveforms(), acquisitions=Acquisitions(), weights={}),
            path=Path(__file__).parent,
        )
        qcm.device.sequencer0.sequence.assert_called_once()
        mock_dump.assert_called_once()

    def test_close_method(self, qcm: QbloxPulsarQCM):
        """Test close method"""
        qcm.close()
        qcm.device.stop_sequencer.assert_called_once()
        qcm.device.close.assert_called_once()  # type: ignore

    def test_close_method_with_value_error(self, qcm: QbloxPulsarQCM):
        """Test close method"""
        qcm.device.stop_sequencer.side_effect = ValueError()
        qcm.close()
        qcm.device.stop_sequencer.assert_called_once()
        qcm.device.close.assert_called_once()  # type: ignore

    def test_not_connected_attribute_error(self, qcm: QbloxPulsarQCM):
        """Test that calling a method when the device is not connected raises an AttributeError."""
        qcm.close()
        with pytest.raises(AttributeError):
            qcm.start_sequencer()

    def test_ip_property(self, qcm: QbloxPulsarQCM):
        """Test ip property."""
        assert qcm.ip == qcm.settings.ip

    def test_id_property(self, qcm: QbloxPulsarQCM):
        """Test id property."""
        assert qcm.id_ == qcm.settings.id_

    def test_name_property(self, qcm: QbloxPulsarQCM):
        """Test name property."""
        assert qcm.name == InstrumentName.QBLOX_QCM

    def test_category_property(self, qcm: QbloxPulsarQCM):
        """Test category property."""
        assert qcm.category == qcm.settings.category

    def test_firmware_property(self, qcm: QbloxPulsarQCM):
        """Test firmware property."""
        assert qcm.firmware == qcm.settings.firmware

    def test_frequency_property(self, qcm: QbloxPulsarQCM):
        """Test frequency property."""
        assert qcm.frequency == qcm.settings.frequency
