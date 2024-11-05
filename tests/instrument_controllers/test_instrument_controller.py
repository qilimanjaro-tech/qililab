"""This file tests the the ``InstrumentController`` class"""

import io

import pytest
from ruamel.yaml import YAML

from qililab.constants import CONNECTION, INSTRUMENTCONTROLLER, RUNCARD
from qililab.instrument_controllers.rohde_schwarz import SGS100AController
from qililab.platform import Platform
from qililab.typings.enums import ConnectionName, InstrumentControllerName, Parameter
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="rs_settings")
def fixture_rs_settings():
    """Fixture that returns an instance of a dummy RS."""
    return {
        RUNCARD.NAME: InstrumentControllerName.ROHDE_SCHWARZ,
        RUNCARD.ALIAS: "rohde_schwarz_controller_0",
        Parameter.REFERENCE_CLOCK.value: "EXT",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.10",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "rs_0",
                "slot_id": 0,
            }
        ],
    }


class TestConnection:
    """This class contains the unit tests for the ``InstrumentController`` class."""

    def test_error_raises_when_no_modules(self, platform: Platform, rs_settings):
        """Test that ensures an error raises when there is no module specifyed

        Args:
            platform (Platform): Platform
        """
        rs_settings[INSTRUMENTCONTROLLER.MODULES] = []
        name = rs_settings.pop(RUNCARD.NAME)
        with pytest.raises(ValueError, match=f"The {name.value} Instrument Controller requires at least ONE module."):
            SGS100AController(settings=rs_settings, loaded_instruments=platform.instruments)

    def test_error_raises_when_no_compatible_number_modules(self, platform: Platform, rs_settings):
        """Error raises when the number of modules of the instument controller
        is not compatible with the modules loded.

        Args:
            platform (Platform): Platform
        """
        rs_settings[INSTRUMENTCONTROLLER.MODULES] = [
            {
                "alias": "rs_0",
                "slot_id": 0,
            },
            {
                "alias": "rs_1",
                "slot_id": 1,
            },
        ]
        name = rs_settings.pop(RUNCARD.NAME)
        with pytest.raises(
            ValueError,
            match=f"The {name.value} Instrument Controller only supports 1 module/s.You have loaded 2 modules.",
        ):
            SGS100AController(settings=rs_settings, loaded_instruments=platform.instruments)

    def test_print_instrument_controllers(self, platform: Platform):
        """Test print instruments."""
        instr_cont = platform.instrument_controllers
        assert str(instr_cont) == str(YAML().dump(instr_cont.to_dict(), io.BytesIO()))

    def test_reset_to_dict(self, platform: Platform):
        """Test that the reset attribute gets reflected when calling the controller to_dict method."""
        instr_cont = platform.instrument_controllers
        controllers_dict = instr_cont.to_dict()

    def test_set_get_reset(self, platform: Platform):
        assert platform.get_parameter(alias="rohde_schwarz_controller_0", parameter=Parameter.RESET) == True
        platform.set_parameter(alias="rohde_schwarz_controller_0", parameter=Parameter.RESET, value=False)
        assert platform.get_parameter(alias="rohde_schwarz_controller_0", parameter=Parameter.RESET) == False

        with pytest.raises(ValueError):
            _ = platform.get_parameter(alias="rohde_schwarz_controller_0", parameter=Parameter.BUS_FREQUENCY)

        with pytest.raises(ValueError):
            _ = platform.set_parameter(alias="rohde_schwarz_controller_0", parameter=Parameter.BUS_FREQUENCY, value=1e9)
