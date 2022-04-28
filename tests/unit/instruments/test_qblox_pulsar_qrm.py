from unittest.mock import MagicMock, patch

import pytest
from qpysequence.sequence import Sequence

from qililab.constants import DEFAULT_PLATFORM_NAME, DEFAULT_SETTINGS_FOLDERNAME
from qililab.instruments import QbloxPulsarQRM
from qililab.settings import SETTINGS_MANAGER

from ..data import qblox_qrm_0_settings_sample


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
        ]
    )
    mock_instance.sequencer0.mock_add_spec(["sync_en", "gain_awg_path0", "gain_awg_path1", "sequence"])
    # connect to instrument
    qrm_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="qblox_qrm_0"
    )
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
        qrm.device.reference_source.assert_called_with(qrm.reference_clock)
        qrm.device.sequencer0.sync_en.assert_called_with(qrm.sync_enabled)

    def test_start_method(self, qrm: QbloxPulsarQRM):
        """Test start method"""
        qrm.start()
        qrm.device.arm_sequencer.assert_called()
        qrm.device.start_sequencer.assert_called()

    def test_setup_method(self, qrm: QbloxPulsarQRM):
        """Test setup method"""
        qrm.setup()
        qrm.device.sequencer0.gain_awg_path0.assert_called_once_with(qrm.gain)
        qrm.device.sequencer0.gain_awg_path1.assert_called_once_with(qrm.gain)
        qrm.device.scope_acq_avg_mode_en_path0.assert_called_once_with(qrm.hardware_average_enabled)
        qrm.device.scope_acq_avg_mode_en_path1.assert_called_once_with(qrm.hardware_average_enabled)
        qrm.device.scope_acq_trigger_mode_path0.assert_called_once_with(qrm.acquire_trigger_mode)
        qrm.device.scope_acq_trigger_mode_path0.assert_called_once_with(qrm.acquire_trigger_mode)

    def test_stop_method(self, qrm: QbloxPulsarQRM):
        """Test stop method"""
        qrm.stop()
        qrm.device.stop_sequencer.assert_called_once()

    def test_reset_method(self, qrm: QbloxPulsarQRM):
        """Test reset method"""
        qrm.reset()
        qrm.device.reset.assert_called_once()

    @patch("qililab.instruments.qblox.qblox_pulsar.yaml.safe_dump", return_value=None)
    def test_upload_method(self, mock_dump: MagicMock, qrm: QbloxPulsarQRM):
        """Test upload method"""
        qrm.upload(sequence=Sequence())
        qrm.device.sequencer0.sequence.assert_called_once()
        mock_dump.assert_called_once()

    def test_get_acquisitions_method(self, qrm: QbloxPulsarQRM):
        """Test get_acquisitions_method"""
        qrm.device.get_acquisitions.return_value = {}
        acquisitions = qrm.get_acquisitions()
        assert isinstance(acquisitions, dict)
        # Assert device calls
        qrm.device.get_sequencer_state.assert_called_once_with(qrm.sequencer, qrm.sequence_timeout)
        qrm.device.get_acquisition_state.assert_called_once_with(qrm.sequencer, qrm.acquisition_timeout)
        qrm.device.store_scope_acquisition.assert_called_once_with(qrm.sequencer, qrm.acquisition_name)
        qrm.device.get_acquisitions.assert_called_once_with(qrm.sequencer)

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

    def test_ip_property(self, qrm: QbloxPulsarQRM):
        """Test ip property."""
        assert qrm.ip == qrm.settings.ip

    def test_id_property(self, qrm: QbloxPulsarQRM):
        """Test id property."""
        assert qrm.id_ == qrm.settings.id_

    def test_name_property(self, qrm: QbloxPulsarQRM):
        """Test name property."""
        assert qrm.name == qrm.settings.name

    def test_category_property(self, qrm: QbloxPulsarQRM):
        """Test category property."""
        assert qrm.category == qrm.settings.category

    def test_acquire_trigger_mode_property(self, qrm: QbloxPulsarQRM):
        """Test acquire_trigger_mode property."""
        assert qrm.acquire_trigger_mode == qrm.settings.acquire_trigger_mode

    def test_hardware_average_enabled_property(self, qrm: QbloxPulsarQRM):
        """Test hardware_average_enabled property."""
        assert qrm.hardware_average_enabled == qrm.settings.hardware_average_enabled

    def test_start_integrate_property(self, qrm: QbloxPulsarQRM):
        """Test start_integrate property."""
        assert qrm.start_integrate == qrm.settings.start_integrate

    def test_sampling_rate_property(self, qrm: QbloxPulsarQRM):
        """Test sampling_rate property."""
        assert qrm.sampling_rate == qrm.settings.sampling_rate

    def test_integration_length_property(self, qrm: QbloxPulsarQRM):
        """Test integration_length property."""
        assert qrm.integration_length == qrm.settings.integration_length

    def test_integration_mode_property(self, qrm: QbloxPulsarQRM):
        """Test integration_mode property."""
        assert qrm.integration_mode == qrm.settings.integration_mode

    def test_sequence_timeout_property(self, qrm: QbloxPulsarQRM):
        """Test sequence_timeout property."""
        assert qrm.sequence_timeout == qrm.settings.sequence_timeout

    def test_acquisition_timeout_property(self, qrm: QbloxPulsarQRM):
        """Test acquisition_timeout property."""
        assert qrm.acquisition_timeout == qrm.settings.acquisition_timeout

    def test_acquisition_name_property(self, qrm: QbloxPulsarQRM):
        """Test acquisition_name property."""
        assert qrm.acquisition_name == qrm.settings.acquisition_name

    def tests_delay_before_readout_property(self, qrm: QbloxPulsarQRM):
        """Test delay_before_readout property."""
        assert qrm.delay_before_readout == qrm.settings.delay_before_readout
