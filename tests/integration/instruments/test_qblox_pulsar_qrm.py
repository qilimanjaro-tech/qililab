import pytest

from qililab.instruments import QbloxPulsarQRM
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.instruments.qblox.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from qililab.typings import CategorySettings


@pytest.fixture(name="qrm")
def fixture_qrm():
    """Return instance of QbloxPulsarQRM class."""
    SETTINGS_MANAGER.platform_name = "platform_0"
    qrm_settings = SETTINGS_MANAGER.load(filename="qrm_0")
    return QbloxPulsarQRM(name="qrm_0", settings=qrm_settings)


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
        assert qrm.settings.category == CategorySettings.QBLOX_QRM
