"""This file tests the the ``qmm_controller`` class"""
import pytest

from qililab.instrument_controllers.quantum_machines import QMMController
from qililab.instruments.quantum_machines import QuantumMachinesManager
from qililab.platform import Platform
from qililab.settings import Settings
from tests.data import SauronQuantumMachines
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronQuantumMachines.runcard)


class TestQMM:
    """This class contains the unit tests for the ``QMMController`` class."""

    @pytest.mark.parametrize("controller_alias", ["qmm_controller", "qmm_with_octave_controller"])
    def test_initialization(self, platform: Platform, controller_alias: str):
        """Test QMMController has been initialized correctly"""
        controller_instance = platform.get_element(alias=controller_alias)
        assert isinstance(controller_instance, QMMController)

        controller_settings = controller_instance.settings
        assert isinstance(controller_settings, Settings)

        controller_modules = controller_instance.modules
        assert len(controller_modules) == 1
        assert isinstance(controller_modules[0], QuantumMachinesManager)
