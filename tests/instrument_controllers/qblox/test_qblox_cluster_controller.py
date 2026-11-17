import copy
import re
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.qblox.qblox_cluster_controller import QbloxClusterController
from qililab.instruments.qblox import QbloxQCM
from qililab.platform import Platform
from qililab.data_management import build_platform


@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard="tests/instrument_controllers/qblox/qblox_runcard.yaml")


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

        controller_instance.device.reference_source.assert_called_once_with(controller_instance.reference_clock)

    @patch("qililab.instrument_controllers.qblox.qblox_cluster_controller.Cluster", autospec=True)
    def test_set_ext_trigger(self, device_mock: MagicMock, platform: Platform):
        """Test set_ext_trigger enables the cluster's external trigger input on the external trigger address."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="cluster_controller")

        controller_instance.connect()

        controller_instance.device.ext_trigger_input_trigger_en = MagicMock()
        controller_instance.device.ext_trigger_input_trigger_address = MagicMock()
        controller_instance.device.ext_trigger_input_delay = MagicMock()
        controller_instance.device.reference_source = MagicMock()
        controller_instance.set_ext_trigger()

        controller_instance.device.ext_trigger_input_trigger_en.assert_called_once_with(True)
        controller_instance.device.ext_trigger_input_trigger_address.assert_called_once_with(15)
        controller_instance.device.ext_trigger_input_delay.assert_called_once_with(0)

    def test_platform_load_warns_on_ext_trigger_in_runcard(self):
        """Loading a runcard that contains ext_trigger must emit a FutureWarning and drop it from to_dict."""
        with pytest.warns(
            FutureWarning,
            match=re.escape(
                "ext_trigger in the runcard is deprecated and will be removed in a future release. "
                "It has no effect: the Qblox cluster's external trigger is now enabled automatically when a "
                "QProgram uses wait_trigger or if_trigger."
            ),
        ):
            platform = build_platform(runcard="tests/instrument_controllers/qblox/qblox_runcard_ext_trigger.yaml")

        controller_instance = platform.instrument_controllers.get_instrument_controller(alias="cluster_controller")
        assert "ext_trigger" not in controller_instance.to_dict()

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
