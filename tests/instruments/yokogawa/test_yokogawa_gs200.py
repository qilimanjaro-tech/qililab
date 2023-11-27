"""Tests for the SGS100A class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.yokogawa.gs200_controller import GS200Controller
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.yokogawa.gs200 import GS200
from qililab.platform import Platform
from qililab.typings.enums import Parameter
from tests.data import SauronYokogawa  # pylint: disable=no-name-in-module
from tests.test_utils import build_platform  # pylint: disable=no-name-in-module, import-error


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronYokogawa.runcard)


@pytest.fixture(name="yokogawa_gs200_controller")
def fixture_yokogawa_gs200_controller(platform: Platform):
    """Return an instance of GS200 controller class"""
    settings = copy.deepcopy(SauronYokogawa.yokogawa_gs200_controller)
    settings.pop("name")
    return GS200Controller(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="yokogawa_gs200")
@patch("qililab.instrument_controllers.yokogawa.gs200_controller.YokogawaGS200", autospec=True)
def fixture_yokogawa_gs200(mock_rs: MagicMock, yokogawa_gs200_controller: GS200Controller):
    """Return connected instance of GS200 class"""
    # add dynamically created attributes
    mock_instance = mock_rs.return_value
    mock_instance.mock_add_spec(["current", "source_mode"])
    yokogawa_gs200_controller.connect()
    return yokogawa_gs200_controller.modules[0]


class TestYokogawaGS200:
    """Unit tests checking the GS200 attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, -0.001),
            (Parameter.CURRENT, 0.0005),
            (Parameter.RAMPING_ENABLED, True),
            (Parameter.RAMPING_ENABLED, False),
            (Parameter.RAMPING_RATE, 0.05),
        ],
    )
    def test_setup_method(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the setup method with float value"""
        assert isinstance(parameter, Parameter)
        yokogawa_gs200.setup(parameter, value)
        if parameter == Parameter.CURRENT:
            assert yokogawa_gs200.current == value
        if parameter == Parameter.RAMPING_ENABLED:
            assert yokogawa_gs200.ramping_enabled == value
        if parameter == Parameter.RAMPING_RATE:
            assert yokogawa_gs200.ramping_rate == value

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.GAIN, 0.0005)])
    def test_setup_method_raises_exception(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the setup method with float value raises an exception with wrong parameters"""
        with pytest.raises(ParameterNotFound):
            yokogawa_gs200.setup(parameter, value)

    def test_to_dict_method(self, yokogawa_gs200: GS200):
        """Test the dict method"""
        assert isinstance(yokogawa_gs200.to_dict(), dict)

    def test_turn_on_method(self, yokogawa_gs200: GS200):
        """Test start method"""
        yokogawa_gs200.turn_on()
        yokogawa_gs200.device.on.assert_called()

    def test_turn_off_method(self, yokogawa_gs200: GS200):
        """Test stop method"""
        yokogawa_gs200.turn_off()
        yokogawa_gs200.device.off.assert_called()

    def test_initial_setup_method(self, yokogawa_gs200: GS200):
        """Test the initial setup method"""
        yokogawa_gs200.initial_setup()
        yokogawa_gs200.device.source_mode.assert_called_with("CURR")

    def test_ramping_enabled_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "ramping_enabled")
        assert yokogawa_gs200.ramping_enabled == yokogawa_gs200.settings.ramping_enabled[0]
        yokogawa_gs200.ramping_enabled = False
        assert yokogawa_gs200.ramping_enabled is False

    def test_ramping_rate_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "ramping_rate")
        assert yokogawa_gs200.ramping_rate == yokogawa_gs200.settings.ramp_rate[0]
        yokogawa_gs200.ramping_rate = 0.05
        assert yokogawa_gs200.ramping_rate == 0.05

    def test_current_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "current")
        assert yokogawa_gs200.current == yokogawa_gs200.settings.current[0]
        yokogawa_gs200.current = 0.01
        yokogawa_gs200.device.ramp_current.assert_called()
        assert yokogawa_gs200.current == 0.01
        yokogawa_gs200.ramping_enabled = False
        yokogawa_gs200.current = 0.0
        yokogawa_gs200.device.current.assert_called()
        assert yokogawa_gs200.current == 0.0
