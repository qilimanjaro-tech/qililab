import copy

import pytest

from qililab.instrument_controllers.yokogawa.gs200_controller import GS200Controller
from qililab.instruments.yokogawa.gs200 import GS200
from qililab.platform import Platform
from qililab.settings import Settings
from tests.data import SauronYokogawa
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronYokogawa.runcard)


@pytest.fixture(name="yokogawa_gs200_controller_wrong_module")
def fixture_yokogawa_gs200_controller_wrong_module(platform: Platform):
    """Return an instance of GS200 controller class"""
    settings = copy.deepcopy(SauronYokogawa.yokogawa_gs200_controller_wrong_module)
    settings.pop("name")
    return GS200Controller(settings=settings, loaded_instruments=platform.instruments)


class TestYokogawaGS200Controller:
    """Unit tests checking the GS200 Controller attributes and methods"""

    def test_initialization(self, platform: Platform):
        """Test QMMController has been initialized correctly"""
        controller_alias = "yokogawa_controller"
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)
        assert isinstance(controller_instance, GS200Controller)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, Settings)

        controller_modules = controller_instance.modules
        assert len(controller_modules) == 1
        assert isinstance(controller_modules[0], GS200)

    def test_check_supported_modules_raises_exception(self, yokogawa_gs200_controller_wrong_module: GS200Controller):
        with pytest.raises(ValueError):
            yokogawa_gs200_controller_wrong_module._check_supported_modules()
