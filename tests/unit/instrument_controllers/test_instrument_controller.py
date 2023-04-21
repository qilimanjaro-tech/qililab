"""This file tests the the ``InstrumentController`` class"""
import copy
import pytest

from qililab.constants import INSTRUMENTCONTROLLER, INSTRUMENTREFERENCE, RUNCARD
from qililab.instrument_controllers.rohde_schwarz import SGS100AController
from qililab.platform import Platform
from qililab.typings.enums import Category
from tests.data import Galadriel


class TestConnection:
    """This class contains the unit tests for the ``InstrumentController`` class."""
    def test_error_raises_when_no_modules(self, platform: Platform):
        """Test that ensures an error raises when there is no module specifyed

        Args:
            platform (Platform): Platform
        """
        settings = copy.deepcopy(Galadriel.rohde_schwarz_controller_0)
        settings[INSTRUMENTCONTROLLER.MODULES] = []
        name = settings.pop(RUNCARD.NAME)
        with pytest.raises(ValueError, match=f"The {name.value} Instrument Controller requires at least ONE module."):
            SGS100AController(settings=settings, loaded_instruments=platform.instruments)

    def test_error_raises_when_no_compatible_number_modules(self, platform: Platform):
        """Error raises when the number of modules of the instument controller
        is not compatible with the modules loded.

        Args:
            platform (Platform): Platform
        """
        settings = copy.deepcopy(Galadriel.rohde_schwarz_controller_0)
        settings[INSTRUMENTCONTROLLER.MODULES] = [
            {
                Category.SIGNAL_GENERATOR.value: "rs_0",
                INSTRUMENTREFERENCE.SLOT_ID: 0,
            },
            {
                Category.SIGNAL_GENERATOR.value: "rs_1",
                INSTRUMENTREFERENCE.SLOT_ID: 1,
            }
        ]
        name = settings.pop(RUNCARD.NAME)
        with pytest.raises(ValueError, match=f"The {name.value} Instrument Controller only supports 1 module/s."
                           + "You have loaded 2 modules."):
            SGS100AController(settings=settings, loaded_instruments=platform.instruments)
