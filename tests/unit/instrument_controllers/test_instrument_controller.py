"""This file tests the the ``InstrumentController`` class"""
import pytest
import copy

from qililab.instrument_controllers import SingleInstrumentController
from tests.data import Galadriel
from qililab.platform import Platform
from qililab.instrument_controllers.rohde_schwarz import SGS100AController

class MiController(SingleInstrumentController):
    def _check_supported_modules(self):
        pass

    def _initialize_device(self):
        pass

@pytest.fixture(name="rohde_schwarz_controller_0")
def fixture_rohde_schwarz_controller_0(platform: Platform):
    """Return connected instance of rohde_schwarz_controller_0 class"""
    settings = copy.deepcopy(Galadriel.rohde_schwarz_controller_0)
    settings.pop("name")
    return SGS100AController(settings=settings, loaded_instruments=platform.instruments)

class TestConnection:
    """This class contains the unit tests for the ``InstrumentController`` class."""
    
    def test_error_raises_when_no_modules(self, rohde_schwarz_controller_0 : SGS100AController):
        with pytest.raises(ValueError, match="The test Instrument Controller requires at least ONE module."):
            rohde_schwarz_controller_0.modules = []
        
    def test_error_raises_when_no_compatible_number_modules(self, rohde_schwarz_controller_0 : SGS100AController):
        with pytest.raises(ValueError, match="The test Instrument Controller requires at least ONE module."):
            rohde_schwarz_controller_0.modules = ['1', '2']