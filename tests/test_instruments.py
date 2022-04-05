import pytest

from qililab.instruments import QbloxPulsarQCM, QbloxPulsarQRM
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from qililab.settings.qblox_pulsar_qrm import QbloxPulsarQRMSettings

SETTINGS_MANAGER.platform_name = "platform_0"


@pytest.fixture
def qcm():
    """Return instance of QbloxPulsarQCM class."""
    return QbloxPulsarQCM(name="qcm_0")


@pytest.fixture
def qrm():
    """Return instance of QbloxPulsarQRM class."""
    return QbloxPulsarQRM(name="qrm_0")


class TestQbloxPulsarQCM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_name(self, qcm: QbloxPulsarQCM):
        """Test name attribute of QbloxPulsarQCM class"""
        assert qcm.name == "qcm_0"

    def test_connected(self, qcm: QbloxPulsarQCM):
        """Test _connected attribute of QbloxPulsarQCM class"""
        assert qcm._connected is False

    def test_settings(self, qcm: QbloxPulsarQCM):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(qcm.settings, QbloxPulsarQCMSettings)

    def test_settings_category(self, qcm: QbloxPulsarQCM):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert qcm.settings.category == "qblox_qcm"

    def test_load_settings(self, qcm: QbloxPulsarQCM):
        """Test load_settings() method of QbloxPulsarQCM class"""
        assert isinstance(qcm.load_settings(), QbloxPulsarQCMSettings)

    def test_load_settings_value_error(self):
        """Test that the class raises a ValueError when the loaded settings are invalid"""
        with pytest.raises(ValueError):
            QbloxPulsarQCM(name="platform")

    def test_getattr_error(self, qcm: QbloxPulsarQCM):
        """Test that the class raises an error when running
        methods without being connected to the instrument."""
        with pytest.raises(AttributeError):
            qcm.setup()


class TestQbloxPulsarQRM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_name(self, qrm: QbloxPulsarQRM):
        """Test name attribute of QbloxPulsarQCM class"""
        assert qrm.name == "qrm_0"

    def test_connected(self, qrm: QbloxPulsarQRM):
        """Test _connected attribute of QbloxPulsarQCM class"""
        assert qrm._connected is False

    def test_settings(self, qrm: QbloxPulsarQRM):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(qrm.settings, QbloxPulsarQRMSettings)

    def test_load_settings(self, qrm: QbloxPulsarQRM):
        """Test load_settings() method of QbloxPulsarQCM class"""
        assert isinstance(qrm.load_settings(), QbloxPulsarQRMSettings)

    def test_settings_category(self, qrm: QbloxPulsarQRM):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert qrm.settings.category == "qblox_qrm"
