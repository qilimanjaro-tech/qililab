import copy
from unittest.mock import patch

import pytest

from qililab.instrument_controllers.keithley.keithley_2400_controller import Keithley2400Controller
from qililab.instruments.keithley.keithley_2400 import Keithley2400
from qililab.platform import Platform
from qililab.settings import Settings
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="keithley_2400_controller_wrong_module")
def fixture_keithley_2400_controller_wrong_module(platform: Platform):
    """Return an instance of Keithley 2400 controller class"""
    settings = copy.deepcopy(Galadriel.keithley_2400_wrong_module)
    settings.pop("name")
    return Keithley2400Controller(settings=settings, loaded_instruments=platform.instruments)


class TestKeithley2400Controller:
    """Unit tests checking the Keithley2400 Controller attributes and methods"""

    def test_initialization(self, platform: Platform):
        """Test Keithley2400 Controller has been initialized correctly"""
        controller_alias = "keithley_2400_controller_0"
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)
        assert isinstance(controller_instance, Keithley2400Controller)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, Settings)

        controller_modules = controller_instance.modules
        assert len(controller_modules) == 1
        assert isinstance(controller_modules[0], Keithley2400)

    def test_initialize_device(self, platform: Platform):
        """Test Keithley2400 Controller initializes the device"""
        controller_alias = "keithley_2400_controller_0"
        controller = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)

        with patch("qililab.instrument_controllers.keithley.keithley_2400_controller.Keithley2400Driver") as mock_driver:
            controller._initialize_device()
            mock_driver.assert_called_once()
            args, kwargs = mock_driver.call_args
            assert kwargs["name"] == f"{controller.name.value}_{controller.alias}"
            assert kwargs["address"] == f"TCPIP0::{controller.address}::INSTR"
            assert kwargs["visalib"] == "@py"
            assert controller.device == mock_driver.return_value

    def test_check_supported_modules_raises_exception(
        self, keithley_2400_controller_wrong_module: Keithley2400Controller
    ):
        with pytest.raises(ValueError):
            keithley_2400_controller_wrong_module._check_supported_modules()
