import pytest

from qililab.instruments import SGS100A, QbloxPulsarQCM, QbloxPulsarQRM
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from qililab.settings.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from qililab.settings.sgs100a import SGS100ASettings

SETTINGS_MANAGER.platform_name = "platform_0"


@pytest.fixture
def qcm():
    """Return instance of QbloxPulsarQCM class."""
    return QbloxPulsarQCM(name="qcm_0")


@pytest.fixture
def qrm():
    """Return instance of QbloxPulsarQRM class."""
    return QbloxPulsarQRM(name="qrm_0")


@pytest.fixture
def rohde_schwarz():
    """Return instance of SGS100A class."""
    return SGS100A(name="rohde_schwarz_0")


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

    def test_check_connected_true(self, qcm: QbloxPulsarQCM):
        """Test check_connected() method of the QbloxPulsarQCM class when _connected is True."""
        qcm._connected = True
        qcm._check_connected()

    def test_check_connected_false(self, qcm: QbloxPulsarQCM):
        """Test check_connected() method of the QbloxPulsarQCM class when _connected is False."""
        with pytest.raises(AttributeError):
            qcm._check_connected()


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

    def test_check_connected_true(self, qrm: QbloxPulsarQRM):
        """Test check_connected() method of the QbloxPulsarQRM class when _connected is True."""
        qrm._connected = True
        qrm._check_connected()

    def test_check_connected_false(self, qrm: QbloxPulsarQRM):
        """Test check_connected() method of the QbloxPulsarQRM class when _connected is False."""
        with pytest.raises(AttributeError):
            qrm._check_connected()


class TestSGS100A:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_name(self, rohde_schwarz: SGS100A):
        """Test name attribute of QbloxPulsarQCM class"""
        assert rohde_schwarz.name == "rohde_schwarz_0"

    def test_connected(self, rohde_schwarz: SGS100A):
        """Test _connected attribute of QbloxPulsarQCM class"""
        assert rohde_schwarz._connected is False

    def test_settings(self, rohde_schwarz: SGS100A):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(rohde_schwarz.settings, SGS100ASettings)

    def test_load_settings(self, rohde_schwarz: SGS100A):
        """Test load_settings() method of QbloxPulsarQCM class"""
        assert isinstance(rohde_schwarz.load_settings(), SGS100ASettings)

    def test_settings_category(self, rohde_schwarz: SGS100A):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert rohde_schwarz.settings.category == "rohde_schwarz"

    def test_check_connected_true(self, rohde_schwarz: SGS100A):
        """Test check_connected() method of the QbloxPulsarQRM class when _connected is True."""
        rohde_schwarz._connected = True
        rohde_schwarz._check_connected()

    def test_check_connected_false(self, rohde_schwarz: SGS100A):
        """Test check_connected() method of the QbloxPulsarQRM class when _connected is False."""
        with pytest.raises(AttributeError):
            rohde_schwarz._check_connected()
