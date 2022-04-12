import pytest

from qililab.instruments import SGS100A, QbloxPulsarQCM, QbloxPulsarQRM
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.instruments.qblox.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from qililab.settings.instruments.qblox.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from qililab.settings.instruments.rohde_schwarz.sgs100a import SGS100ASettings

SETTINGS_MANAGER.platform_name = "platform_0"


@pytest.fixture(name="qcm")
def fixture_qcm():
    """Return instance of QbloxPulsarQCM class."""
    qcm_settings = SETTINGS_MANAGER.load(filename="qcm_0")
    return QbloxPulsarQCM(name="qcm_0", settings=qcm_settings)


@pytest.fixture(name="qrm")
def fixture_qrm():
    """Return instance of QbloxPulsarQRM class."""
    qrm_settings = SETTINGS_MANAGER.load(filename="qrm_0")
    return QbloxPulsarQRM(name="qrm_0", settings=qrm_settings)


@pytest.fixture(name="rohde_schwarz")
def fixture_rohde_schwarz():
    """Return instance of SGS100A class."""
    rs_settings = SETTINGS_MANAGER.load(filename="rohde_schwarz_0")
    return SGS100A(name="rohde_schwarz_0", settings=rs_settings)


class TestQbloxPulsarQCM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_name(self, qcm: QbloxPulsarQCM):
        """Test name attribute of QbloxPulsarQCM class"""
        assert qcm.name == "qcm_0"

    def test_settings(self, qcm: QbloxPulsarQCM):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(qcm.settings, QbloxPulsarQCMSettings)

    def test_settings_category(self, qcm: QbloxPulsarQCM):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert qcm.settings.category == "qblox_qcm"

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

    def test_settings(self, qrm: QbloxPulsarQRM):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(qrm.settings, QbloxPulsarQRMSettings)

    def test_settings_category(self, qrm: QbloxPulsarQRM):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert qrm.settings.category == "qblox_qrm"


class TestSGS100A:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_name(self, rohde_schwarz: SGS100A):
        """Test name attribute of QbloxPulsarQCM class"""
        assert rohde_schwarz.name == "rohde_schwarz_0"

    def test_settings(self, rohde_schwarz: SGS100A):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(rohde_schwarz.settings, SGS100ASettings)

    def test_settings_category(self, rohde_schwarz: SGS100A):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert rohde_schwarz.settings.category == "rohde_schwarz"
