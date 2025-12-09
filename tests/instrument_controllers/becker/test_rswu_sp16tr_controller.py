import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.becker.rswu_sp16tr_controller import RSWUSP16TRController
from qililab.instruments.becker.rswu_sp16tr import RSWUSP16TR
from qililab.platform import Platform
from qililab.settings import Settings
from qililab.typings import ConnectionName
from tests.data import SauronRSWUSP16TR
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronRSWUSP16TR.runcard)


@pytest.fixture(name="rswu_sp16tr_controller_wrong_module")
def fixture_rswu_sp16tr_controller_wrong_module_wrong_module(platform: Platform) -> RSWUSP16TRController:
    """Return an instance of the rswu_sp16tr controller with an incorrect module."""
    settings = copy.deepcopy(SauronRSWUSP16TR.rswu_sp16tr_controller_wrong_module)
    settings.pop("name")
    return RSWUSP16TRController(settings=settings, loaded_instruments=platform.instruments)



class TestRSWUSP16TRController:
    """Unit tests checking the RSWUSP16TR controller attributes and methods"""

    def test_initialization(self, platform: Platform):
        """Test RSWUSP16TR controller has been initialized correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="rswu_sp16tr")
        assert isinstance(controller_instance, RSWUSP16TRController)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, Settings)

        controller_modules = controller_instance.modules
        assert len(controller_modules) == 1
        assert isinstance(controller_modules[0], RSWUSP16TR)

    @patch("qililab.instrument_controllers.becker.rswu_sp16tr_controller.BeckerRSWUSP16TR", autospec=True)
    def test_initialize_device(self, device_mock: MagicMock, platform: Platform):
        """Test RSWUSP16TR controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="rswu_sp16tr")

        controller_instance._initialize_device()

        device_mock.assert_called_once_with(
            name=f"{controller_instance.name.value}_{controller_instance.alias}", address=f"TCPIP::{controller_instance.address}::5025::SOCKET", visalib="@py"
        )

    def test_check_supported_modules_raises_exception(self, platform:Platform):
        """Test RSWUSP16TR controller raises an error if initialized with wrong module."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="wrong_rswu_sp16tr")
        with pytest.raises(ValueError):
            controller_instance._check_supported_modules()