import copy
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.qblox.qblox_spi_rack_controller import QbloxSPIRackController
from qililab.instruments.qblox import QbloxS4g
from qililab.platform import Platform
from tests.data import SauronSpiRack
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronSpiRack.runcard)


class TestQbloxSpiRackController:
    """Unit tests checking the SPI rack controller attributes and methods"""

    def test_initialization(self, platform: Platform):
        """Test SPI rack controller has been initialized correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="spi_controller_usb")
        assert isinstance(controller_instance, QbloxSPIRackController)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, QbloxSPIRackController.QbloxSPIRackControllerSettings)

        controller_modules = controller_instance.modules
        assert len(controller_modules) == 1
        assert isinstance(controller_modules[0], QbloxS4g)

    @patch("qililab.instrument_controllers.qblox.qblox_spi_rack_controller.SPI_Rack", autospec=True)
    def test_initialize_device(self, device_mock: MagicMock, platform: Platform):
        """Test SPI rack controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="spi_controller_usb")

        controller_instance._initialize_device()

        device_mock.assert_called_once_with(
            name=f"{controller_instance.name.value}_{controller_instance.alias}",
            address=f"/dev/{controller_instance.address}",
        )

    @patch("qililab.instrument_controllers.qblox.qblox_spi_rack_controller.SPI_Rack", autospec=True)
    def test_set_device_to_all_modules(self, device_mock: MagicMock, platform: Platform):
        """Test SPI rack controller initializes device correctly foa all modules."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="spi_controller_usb")

        controller_instance._initialize_device()
        controller_instance.device = mock.Mock()
        controller_instance._set_device_to_all_modules()

        controller_instance.device.add_spi_module.assert_called_once()

    @patch("qililab.instrument_controllers.qblox.qblox_spi_rack_controller.SPI_Rack", autospec=True)
    def test_module(self, device_mock: MagicMock, platform: Platform):
        """Test SPI rack controller sets module correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="spi_controller_usb")

        controller_instance._initialize_device()
        controller_instance.device = mock.Mock()
        controller_instance.module(1)

        assert controller_instance.module(1) == getattr(controller_instance.device, f"module{1}")

    def test_check_supported_modules_raises_exception(self, platform: Platform):
        """Test SPI rack controller raises an error if initialized with wrong module."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(
            alias="spi_controller_wrong_module"
        )
        with pytest.raises(ValueError):
            controller_instance._check_supported_modules()
