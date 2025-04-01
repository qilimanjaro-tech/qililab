"""Tests for the E5080B class."""
import io
import copy
import re
import warnings
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments.keysight import E5080B
from qililab.typings.enums import Parameter
from ruamel.yaml import YAML

from qililab.constants import CONNECTION, INSTRUMENTCONTROLLER, RUNCARD
from qililab.instrument_controllers.vector_network_analyzer import E5080BController
from qililab.platform import Platform
from qililab.typings.enums import ConnectionName, InstrumentControllerName, Parameter
from tests.data import SauronVNA
from tests.test_utils import build_platform

@pytest.fixture(name="e5080b")
def fixture_e5080b() -> E5080B:
    """Fixture that returns an instance of a dummy QDAC-II."""
    e5080b = E5080B(
        {
            "alias": "vna",
            Parameter.SOURCE_POWER.value: 10,
            # Parameter.FREQUENCY_START.value: 1e6,
            Parameter.FREQUENCY_STOP.value: 8e9,
            Parameter.FREQUENCY_CENTER.value: 4e9,
            Parameter.STEP_AUTO.value: False,
            Parameter.STEP_SIZE.value: 1e6,
            Parameter.SPAN.value: 7.99e9,
            Parameter.CW_FREQUENCY.value: 4e9,
            Parameter.NUMBER_POINTS.value: 201,
            Parameter.SOURCE_POWER.value: 10,
            Parameter.IF_BANDWIDTH.value: 1e3,
            Parameter.SWEEP_TYPE.value: "lin",
            Parameter.SWEEP_MODE.value: "cont",
            Parameter.SCATTERING_PARAMETER.value: "S21",
            Parameter.AVERAGES_ENABLED.value: True,
            Parameter.NUMBER_AVERAGES.value: 16,
            Parameter.AVERAGES_MODE.value: "Point",
            Parameter.FORMAT_DATA.value: "real,32",
        }
    )
    e5080b.device = MagicMock()
    return e5080b

@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronVNA.runcard)

@pytest.fixture(name="e5080b_controller")
def fixture_e5080b_controller(sauron_platform: Platform):
    """Return an instance of VectorNetworkAnalyzer controller class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b_controller)
    settings.pop("name")
    return E5080BController(settings=settings, loaded_instruments=sauron_platform.instruments)

@pytest.fixture(name="e5080b_no_device")
def fixture_e5080b_no_device():
    """Return an instance of VectorNetworkAnalyzer class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b)
    settings.pop("name")
    return E5080B(settings=settings)

@pytest.fixture(name="e5080b_settings")
def fixture_e5080b_settings():
    """Fixture that returns an instance of a dummy VNA."""
    return {
        RUNCARD.NAME: InstrumentControllerName.KEYSIGHT_E5080B,
        RUNCARD.ALIAS: "keysight_e5080b",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.10",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "keysight_e5080b",
                "slot_id": 0,
            }
        ],
    }

# @pytest.fixture(name="e5080b")
# @patch(
#     "qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller.E5080BController",
#     autospec=True,
# )
# def fixture_e5080b(mock_device: MagicMock, e5080b_controller: E5080BController):
#     """Return connected instance of VectorNetworkAnalyzer class"""
#     mock_instance = mock_device.return_value
#     e5080b_controller.connect()
#     mock_device.assert_called()
#     return e5080b_controller.modules[0]

class TestE5080B:
    """Unit tests checking the E5080B attributes and methods"""
  

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.SOURCE_POWER, 0.01),
        ],
    )
    def test_set_parameter_method(
        self,
        e5080b: E5080B,
        parameter: Parameter,
        value: float,
    ):
        """Test setup method"""
        e5080b.set_parameter(parameter=parameter, value=value)
        if parameter == Parameter.SOURCE_POWER:
            assert e5080b.settings.source_power == value

    def test_error_raises_when_no_modules(self, platform: Platform, e5080b_settings):
        """Test that ensures an error raises when there is no module specifyed

        Args:
            platform (Platform): Platform
        """
        e5080b_settings[INSTRUMENTCONTROLLER.MODULES] = []
        name = e5080b_settings.pop(RUNCARD.NAME)
        with pytest.raises(ValueError, match=f"The {name.value} Instrument Controller requires at least ONE module."):
            E5080BController(settings=e5080b_settings, loaded_instruments=platform.instruments)


    def test_print_instrument_controllers(self, platform: Platform):
        """Test print instruments."""
        instr_cont = platform.instrument_controllers
        assert str(instr_cont) == str(YAML().dump(instr_cont.to_dict(), io.BytesIO()))

    def test_to_dict_method(self, e5080b_no_device: E5080B):
        """Test the dict method"""
        assert isinstance(e5080b_no_device.to_dict(), dict)

    def test_turn_on_method(self, e5080b: E5080B):
        """Test turn_on method"""
        e5080b.turn_on()

    def test_turn_off_method(self, e5080b: E5080B):
        """Test turn_off method"""
        e5080b.turn_off()

    def test_reset_method(self, e5080b: E5080B):
        """Test reset method"""
        e5080b.reset()
    
    @pytest.mark.parametrize(
        "parameter, expected_value",
        [
            (Parameter.SOURCE_POWER, 10),
        ],
    )
    def test_get_parameter_method(
        self,
        e5080b: E5080B,
        parameter: Parameter,
        expected_value: float,
    ):
        """Test get_parameter method"""
        value = e5080b.get_parameter(parameter=parameter)
        assert value == expected_value
