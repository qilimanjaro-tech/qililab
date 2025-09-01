import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.qblox.qblox_cluster_controller import QbloxClusterController
from qililab.instruments.qblox import QbloxQCM
from qililab.platform import Platform
from qililab.data_management import build_platform


@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard="tests/instrument_controllers/qblox/qblox_runcard.yaml")


@pytest.fixture(name="platform_ext_trigger")
def fixture_platform_ext_trigger():
    return build_platform(runcard="tests/instrument_controllers/qblox/qblox_runcard_ext_trigger.yaml")


class TestQbloxClusterController:
    """Unit tests checking the QDAC-II controller attributes and methods"""

    def test_initialization(self, platform: Platform):
        """Test QDAC-II controller has been initialized correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="cluster_controller")
        assert isinstance(controller_instance, QbloxClusterController)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, QbloxClusterController.QbloxClusterControllerSettings)

        controller_modules = controller_instance.modules
        assert len(controller_modules) == 1
        assert isinstance(controller_modules[0], QbloxQCM)

    @patch("qililab.instrument_controllers.qblox.qblox_cluster_controller.Cluster", autospec=True)
    def test_initialize_device(self, device_mock: MagicMock, platform: Platform):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="cluster_controller")

        controller_instance._initialize_device()

        device_mock.assert_called_once_with(
            name=f"{controller_instance.name.value}_{controller_instance.alias}", identifier=controller_instance.address
        )

    @patch("qililab.instrument_controllers.qblox.qblox_cluster_controller.Cluster", autospec=True)
    def test_initial_setup(self, device_mock: MagicMock, platform: Platform):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="cluster_controller")

        controller_instance.connect()

        controller_instance.device.reference_source = MagicMock()
        controller_instance.initial_setup()

        controller_instance.device.reference_source.assert_called_once_with(controller_instance.reference_clock.value)

    @patch("qililab.instrument_controllers.qblox.qblox_cluster_controller.Cluster", autospec=True)
    def test_initial_setup_ext_trigger(self, device_mock: MagicMock, platform_ext_trigger: Platform):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform_ext_trigger.instrument_controllers.get_instrument_controller(
            alias="cluster_controller"
        )

        controller_instance.connect()

        controller_instance.device.ext_trigger_input_trigger_en = MagicMock()
        controller_instance.device.ext_trigger_input_trigger_address = MagicMock()
        controller_instance.device.ext_trigger_input_delay = MagicMock()
        controller_instance.device.reference_source = MagicMock()
        controller_instance.initial_setup()

        controller_instance.device.ext_trigger_input_trigger_en.assert_called_once_with(True)
        controller_instance.device.ext_trigger_input_trigger_address.assert_called_once_with(15)
        controller_instance.device.ext_trigger_input_delay.assert_called_once_with(0)

    @patch("qililab.instrument_controllers.qblox.qblox_cluster_controller.Cluster", autospec=True)
    def test_reset(self, device_mock: MagicMock, platform: Platform):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="cluster_controller")
        for module in controller_instance.modules:
            module.clear_cache = MagicMock()

        controller_instance.connect()
        controller_instance.reset()

        controller_instance.device.reset.assert_called_once()
        for module in controller_instance.modules:
            module.clear_cache.assert_called_once()

    def test_check_supported_modules_raises_exception(self, platform: Platform):
        """Test QDAC-II controller raises an error if initialized with wrong module."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(
            alias="cluster_controller_wrong_module"
        )
        with pytest.raises(ValueError):
            controller_instance._check_supported_modules()
