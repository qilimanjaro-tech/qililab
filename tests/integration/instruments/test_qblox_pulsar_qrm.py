import pytest

from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.instruments import QbloxPulsarQRM
from qililab.settings import SETTINGS_MANAGER
from qililab.typings import CategorySettings


@pytest.fixture(name="qrm")
def fixture_qrm():
    """Return instance of QbloxPulsarQRM class."""
    qrm_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name="platform_0", filename="qblox_qrm_0"
    )
    return QbloxPulsarQRM(settings=qrm_settings)


class TestQbloxPulsarQRM:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_settings_category(self, qrm: QbloxPulsarQRM):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert qrm.category == CategorySettings.QUBIT_READOUT
