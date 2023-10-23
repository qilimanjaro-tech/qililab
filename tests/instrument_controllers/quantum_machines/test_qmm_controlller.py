"""This file tests the the ``qmm_controller`` class"""
from unittest.mock import MagicMock
import pytest

from qililab.instrument_controllers.quantum_machines import QMMController
from qililab.instruments.quantum_machines import QMM
from qililab.platform import Platform
from qililab.settings import Settings
from qililab.typings import QMMDriver
from qililab.typings.enums import InstrumentControllerName
from tests.data import Galadriel
from tests.test_utils import build_platform

@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)

class TestQMM:
    """This class contains the unit tests for the ``QMMController`` class."""

    def test_initialization(self, platform: Platform):
        """Test QMMController has been initialized correctly"""
        controller_alias = "qmm_controller_0"
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)
        print(platform.instrument_controllers)
        assert isinstance(controller_instance, QMMController)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, Settings)

        controller_modules = controller_instance.modules
        assert len(controller_modules)==1
        assert isinstance(controller_modules[0], QMM)
