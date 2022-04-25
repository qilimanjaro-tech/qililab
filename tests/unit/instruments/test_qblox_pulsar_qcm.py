from unittest.mock import MagicMock, patch

import pytest

from qililab.constants import DEFAULT_PLATFORM_NAME, DEFAULT_SETTINGS_FOLDERNAME
from qililab.instruments import QbloxPulsarQCM
from qililab.settings import SETTINGS_MANAGER

from ..data import qblox_qcm_0_settings_sample


@pytest.fixture(name="qcm")
@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
@patch("qililab.settings.settings_manager.yaml.safe_load", return_value=qblox_qcm_0_settings_sample)
def fixture_qcm(mock_load: MagicMock, mock_pulsar: MagicMock):
    """Return connected instance of QbloxPulsarQCM class"""
    # add dynamically created attributes
    mock_instance = mock_pulsar.return_value
    mock_instance.mock_add_spec(["reference_source", "sequencer0"])
    mock_instance.sequencer0.mock_add_spec(["sync_en", "gain_awg_path0", "gain_awg_path1", "sequence"])
    # connect to instrument
    qcm_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="qblox_qcm_0"
    )
    mock_load.assert_called_once()
    qcm = QbloxPulsarQCM(settings=qcm_settings)
    qcm.connect()
    return qcm


class TestQbloxPulsarQCM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_connect_method_raises_error(self, qcm: QbloxPulsarQCM):
        """Test that calling again connect raises a ValueError"""
        with pytest.raises(ValueError):
            qcm.connect()

    def test_inital_setup_method(self, qcm: QbloxPulsarQCM):
        """Test initial_setup method"""
        qcm.initial_setup()
        qcm.device.reference_source.assert_called_with(qcm.reference_clock)
        qcm.device.sequencer0.sync_en.assert_called_with(qcm.sync_enabled)

    def test_start_method(self, qcm: QbloxPulsarQCM):
        """Test start method"""
        qcm.start()
        qcm.device.arm_sequencer.assert_called()
        qcm.device.start_sequencer.assert_called()

    def test_setup_method(self, qcm: QbloxPulsarQCM):
        """Test setup method"""
        qcm.setup()
        qcm.device.sequencer0.gain_awg_path0.assert_called_once_with(qcm.gain)
        qcm.device.sequencer0.gain_awg_path1.assert_called_once_with(qcm.gain)

    def test_stop_method(self, qcm: QbloxPulsarQCM):
        """Test stop method"""
        qcm.stop()
        qcm.device.stop_sequencer.assert_called_once()

    def test_reset_method(self, qcm: QbloxPulsarQCM):
        """Test reset method"""
        qcm.reset()
        qcm.device.reset.assert_called_once()

    def test_upload_method(self, qcm: QbloxPulsarQCM):
        """Test upload method"""
        path = "dummy_path"
        qcm.upload(sequence_path=path)
        qcm.device.sequencer0.sequence.assert_called_once_with(path)

    def test_close_method(self, qcm: QbloxPulsarQCM):
        """Test close method"""
        qcm.close()
        qcm.device.stop_sequencer.assert_called_once()
        qcm.device.close.assert_called_once()

    def test_not_connected_attribute_error(self, qcm: QbloxPulsarQCM):
        """Test that calling a method when the device is not connected raises an AttributeError."""
        qcm.close()
        with pytest.raises(AttributeError):
            qcm.start()
