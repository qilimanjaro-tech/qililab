import pytest

from qililab.constants import DEFAULT_PLATFORM_NAME, DEFAULT_SETTINGS_FOLDERNAME
from qililab.instruments import QbloxPulsarQCM
from qililab.settings import SETTINGS_MANAGER
from qililab.typings import Category


@pytest.fixture(name="qcm")
def fixture_qcm():
    """Return instance of QbloxPulsarQCM class."""
    qcm_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="qblox_qcm_0"
    )
    return QbloxPulsarQCM(settings=qcm_settings)


class TestQbloxPulsarQCM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_settings_category(self, qcm: QbloxPulsarQCM):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert qcm.category == Category.AWG

    def test_getattr_error(self, qcm: QbloxPulsarQCM):
        """Test that the class raises an error when running
        methods without being connected to the instrument."""
        with pytest.raises(AttributeError):
            qcm.setup()
