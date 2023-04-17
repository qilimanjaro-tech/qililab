"""This file tests the the ``InstrumentController`` class"""
import pytest
import copy

from qililab.constants import INSTRUMENTCONTROLLER, RUNCARD, INSTRUMENTREFERENCE
from qililab.typings.enums import Category

from qililab.instrument_controllers import SingleInstrumentController
from tests.data import Galadriel
from qililab.platform import Platform
from qililab.instrument_controllers.rohde_schwarz import SGS100AController


class TestConnection:
    """This class contains the unit tests for the ``InstrumentController`` class."""
    
    def test_error_raises_when_no_modules(self, platform: Platform):
        settings = copy.deepcopy(Galadriel.rohde_schwarz_controller_0)
        settings[INSTRUMENTCONTROLLER.MODULES] = []
        name = settings.pop(RUNCARD.NAME)
        with pytest.raises(ValueError, match=f"The {name.value} Instrument Controller requires at least ONE module."):
            SGS100AController(settings=settings, loaded_instruments=platform.instruments)

    def test_error_raises_when_no_compatible_number_modules(self, platform: Platform):
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
        with pytest.raises(ValueError, match=f"The {name.value} Instrument Controller only supports 1 module/s.You have loaded 2 modules."):
            SGS100AController(settings=settings, loaded_instruments=platform.instruments)