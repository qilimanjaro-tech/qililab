from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments import QbloxPulsarQRM
from qililab.settings import SETTINGS_MANAGER

from .data import qrm_0_settings_sample


@pytest.fixture(name="qrm")
@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
@patch("qililab.settings.settings_manager.yaml.load", return_value=qrm_0_settings_sample)
def fixture_qrm(mock_load: MagicMock, mock_pulsar: MagicMock):
    """Return connected instance of QbloxPulsarQRM class"""
    SETTINGS_MANAGER.platform_name = "platform_0"
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
        ]
    )
    mock_instance.sequencer0.mock_add_spec(["sync_en", "gain_awg_path0", "gain_awg_path1"])
    # connect to instrument
    SETTINGS_MANAGER.platform_name = "platform_0"
    qrm_settings = SETTINGS_MANAGER.load(filename="qrm_0")
    mock_load.assert_called_once()
    qrm = QbloxPulsarQRM(settings=qrm_settings)
    qrm.connect()
    return qrm


class TestQbloxPulsarQRM:
    """Unit tests checking the QbloxPulsarQRM attributes and methods"""

    def test_connect_method_raises_error(self, qrm: QbloxPulsarQRM):
        """Test that calling again connect raises a ValueError"""
        with pytest.raises(ValueError):
            qrm.connect()

    def test_inital_setup_method(self, qrm: QbloxPulsarQRM):
        """Test initial_setup method"""
        qrm.initial_setup()
        qrm.device.reference_source.assert_called_with(qrm.settings.reference_clock)
        qrm.device.sequencer0.sync_en.assert_called_with(qrm.settings.sync_enabled)

    def test_start_method(self, qrm: QbloxPulsarQRM):
        """Test start method"""
        qrm.start()
        qrm.device.arm_sequencer.assert_called()
        qrm.device.start_sequencer.assert_called()

    def test_setup_method(self, qrm: QbloxPulsarQRM):
        """Test setup method"""
        qrm.setup()
        qrm.device.sequencer0.gain_awg_path0.assert_called_once_with(qrm.settings.gain)
        qrm.device.sequencer0.gain_awg_path1.assert_called_once_with(qrm.settings.gain)
        qrm.device.scope_acq_avg_mode_en_path0.assert_called_once_with(qrm.settings.hardware_average_enabled)
        qrm.device.scope_acq_avg_mode_en_path1.assert_called_once_with(qrm.settings.hardware_average_enabled)
        qrm.device.scope_acq_trigger_mode_path0.assert_called_once_with(qrm.settings.acquire_trigger_mode)
        qrm.device.scope_acq_trigger_mode_path0.assert_called_once_with(qrm.settings.acquire_trigger_mode)

    def test_stop_method(self, qrm: QbloxPulsarQRM):
        """Test stop method"""
        qrm.stop()
        qrm.device.stop_sequencer.assert_called_once()

    def test_reset_method(self, qrm: QbloxPulsarQRM):
        """Test reset method"""
        qrm.reset()
        qrm.device.reset.assert_called_once()

    def test_upload_method(self, qrm: QbloxPulsarQRM):
        """Test upload method"""
        qrm.device.sequencer0.mock_add_spec(["sequence"])
        path = "dummy_path"
        qrm.upload(sequence_path=path)
        qrm.device.sequencer0.sequence.assert_called_once_with(path)

    def test_get_acquisitions_method(self, qrm: QbloxPulsarQRM):
        """Test get_acquisitions_method"""
        qrm.device.get_acquisitions.return_value = {}
        acquisitions = qrm.get_acquisitions()
        assert isinstance(acquisitions, dict)
        # Assert device calls
        qrm.device.get_sequencer_state.assert_called_once_with(qrm.settings.sequencer, qrm.settings.sequence_timeout)
        qrm.device.get_acquisition_state.assert_called_once_with(
            qrm.settings.sequencer, qrm.settings.acquisition_timeout
        )
        qrm.device.store_scope_acquisition.assert_called_once_with(
            qrm.settings.sequencer, qrm.settings.acquisition_name
        )
        qrm.device.get_acquisitions.assert_called_once_with(qrm.settings.sequencer)

    def test_close_method(self, qrm: QbloxPulsarQRM):
        """Test close method"""
        qrm.close()
        qrm.device.stop_sequencer.assert_called_once()
        qrm.device.close.assert_called_once()

    def test_not_connected_attribute_error(self, qrm: QbloxPulsarQRM):
        """Test that calling a method when the device is not connected raises an AttributeError."""
        qrm.close()
        with pytest.raises(AttributeError):
            qrm.start()
