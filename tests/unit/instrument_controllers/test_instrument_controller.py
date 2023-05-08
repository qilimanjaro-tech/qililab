"""This file tests the the ``InstrumentController`` class"""
import pytest

from qililab.constants import CONNECTION, INSTRUMENTCONTROLLER, INSTRUMENTREFERENCE, RUNCARD
from qililab.instrument_controllers.rohde_schwarz import SGS100AController
from qililab.platform import Platform
from qililab.typings.enums import Category, ConnectionName, InstrumentControllerName, InstrumentControllerSubCategory


@pytest.fixture(name="rs_settings")
def fixture_rs_settings():
    """Fixture that returns an instance of a dummy RS."""
    return {
        RUNCARD.ID: 2,
        RUNCARD.NAME: InstrumentControllerName.ROHDE_SCHWARZ,
        RUNCARD.ALIAS: "rohde_schwarz_controller_0",
        RUNCARD.CATEGORY: Category.INSTRUMENT_CONTROLLER.value,
        RUNCARD.SUBCATEGORY: InstrumentControllerSubCategory.SINGLE.value,
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "192.168.0.10",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                Category.SIGNAL_GENERATOR.value: "rs_0",
                INSTRUMENTREFERENCE.SLOT_ID: 0,
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
                Category.SIGNAL_GENERATOR.value: "rs_0",
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            },
            {
                Category.SIGNAL_GENERATOR.value: "rs_1",
                INSTRUMENTREFERENCE.SLOT_ID: 1,
            },
        ]
        name = rs_settings.pop(RUNCARD.NAME)
        with pytest.raises(
            ValueError,
            match=f"The {name.value} Instrument Controller only supports 1 module/s.You have loaded 2 modules.",
        ):
            SGS100AController(settings=rs_settings, loaded_instruments=platform.instruments)
