import pytest

from qililab.instruments import QbloxPulsarQCM
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.instruments.qblox.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from qililab.typings import CategorySettings

SETTINGS_MANAGER.platform_name = "platform_0"


@pytest.fixture(name="qcm")
def fixture_qcm():
    """Return instance of QbloxPulsarQCM class."""
    qcm_settings = SETTINGS_MANAGER.load(filename="qblox_qcm_0")
    return QbloxPulsarQCM(settings=qcm_settings)


class TestQbloxPulsarQCM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_settings(self, qcm: QbloxPulsarQCM):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(qcm.settings, QbloxPulsarQCMSettings)

    def test_settings_category(self, qcm: QbloxPulsarQCM):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert qcm.settings.category == CategorySettings.QUBIT_CONTROL

    def test_getattr_error(self, qcm: QbloxPulsarQCM):
        """Test that the class raises an error when running
        methods without being connected to the instrument."""
        with pytest.raises(AttributeError):
            qcm.setup()
