import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.qdevil.qdevil_qdac2_controller import QDevilQDac2Controller
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.platform import Platform
from qililab.settings import Settings
from qililab.typings import ConnectionName
from tests.data import SauronQDevil
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronQDevil.runcard)


@pytest.fixture(name="qdevil_qdac2_controller_wrong_module")
def fixture_qdevil_qdac2_controller_wrong_module_wrong_module(platform: Platform) -> QDevilQDac2Controller:
    """Return an instance of the QDAC-II controller with an incorrect module."""
    settings = copy.deepcopy(SauronQDevil.qdevil_qdac2_controller_wrong_module)
    settings.pop("name")
    return QDevilQDac2Controller(settings=settings, loaded_instruments=platform.instruments)


class TestQDevilQDac2Controller:
    """Unit tests checking the QDAC-II controller attributes and methods"""

    @pytest.mark.parametrize("controller_alias", ["qdac_controller_ip", "qdac_controller_usb"])
    def test_initialization(self, platform: Platform, controller_alias: str):
        """Test QDAC-II controller has been initialized correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)
        assert isinstance(controller_instance, QDevilQDac2Controller)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, Settings)

        controller_modules = controller_instance.modules
        assert len(controller_modules) == 1
        assert isinstance(controller_modules[0], QDevilQDac2)

    @patch("qililab.instrument_controllers.qdevil.qdevil_qdac2_controller.QDevilQDac2Device", autospec=True)
    @pytest.mark.parametrize("controller_alias", ["qdac_controller_ip", "qdac_controller_usb"])
    def test_initialize_device(self, device_mock: MagicMock, platform: Platform, controller_alias: str):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)

        controller_instance._initialize_device()

        name = f"{controller_instance.name.value}_{controller_instance.alias}"
        address = (
            f"TCPIP::{controller_instance.address}::5025::SOCKET"
            if controller_instance.connection.name == ConnectionName.TCP_IP
            else f"ASRL/dev/{controller_instance.address}::INSTR"
        )
        device_mock.assert_called_once_with(name, address)

    def test_check_supported_modules_raises_exception(
        self, qdevil_qdac2_controller_wrong_module: QDevilQDac2Controller
    ):
        """Test QDAC-II controller raises an error if initialized with wrong module."""
        with pytest.raises(ValueError):
            qdevil_qdac2_controller_wrong_module._check_supported_modules()
