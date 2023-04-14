"""This file tests the the ``InstrumentController`` class"""
import pytest

from unittest.mock import MagicMock
from qililab.instrument_controllers import SingleInstrumentController

class MiController(SingleInstrumentController):
    def _check_supported_modules(self):
        pass

    def _initialize_device(self):
        pass


class TestConnection:
    """This class contains the unit tests for the ``InstrumentController`` class."""

    def test_error_raises_when_no_modules(self):
        with pytest.raises(ValueError) as e:
            test = MiController(settings = {'id_':'test', 'category':'test', 'connection':'test', 'modules':'test', 'subcategory':'test'}, loaded_instruments = [])
            test.name = "test"
            test.modules = []
            assert str(e.value) == "The test Instrument Controller requires at least ONE module."
