import pytest

from qililab.instruments import SGS100A
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.instruments.rohde_schwarz.sgs100a import SGS100ASettings
from qililab.typings import CategorySettings

SETTINGS_MANAGER.platform_name = "platform_0"


@pytest.fixture(name="rohde_schwarz")
def fixture_rohde_schwarz():
    """Return instance of SGS100A class."""
    rs_settings = SETTINGS_MANAGER.load(filename="rohde_schwarz_0")
    return SGS100A(settings=rs_settings)


class TestSGS100A:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_settings(self, rohde_schwarz: SGS100A):
        """Test settings attribute type of QbloxPulsarQCM class"""
        assert isinstance(rohde_schwarz.settings, SGS100ASettings)

    def test_settings_category(self, rohde_schwarz: SGS100A):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert rohde_schwarz.settings.category == CategorySettings.SIGNAL_GENERATOR
