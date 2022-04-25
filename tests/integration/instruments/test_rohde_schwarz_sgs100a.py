import pytest

from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.instruments import SGS100A
from qililab.settings import SETTINGS_MANAGER
from qililab.typings import Category


@pytest.fixture(name="rohde_schwarz")
def fixture_rohde_schwarz():
    """Return instance of SGS100A class."""
    rs_settings = SETTINGS_MANAGER.load(
        foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name="platform_0", filename="rohde_schwarz_0"
    )
    return SGS100A(settings=rs_settings)


class TestSGS100A:
    """Unit tests checking the QbloxPulsarQCM attributes and methods"""

    def test_settings_category(self, rohde_schwarz: SGS100A):
        """Test category attribute of settings attribute of QbloxPulsarQCM class"""
        assert rohde_schwarz.category == Category.SIGNAL_GENERATOR
