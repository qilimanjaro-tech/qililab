""" Unit testing module for the Factory of instrument drivers"""
import pytest
from qcodes.instrument.instrument import Instrument

from qililab.drivers.instruments import GS200, Cluster, ERASynthPlus, Keithley2600, Pulsar, RhodeSchwarzSGS100A, SpiRack
from qililab.drivers.instruments.instrument_factory import InstrumentDriverFactory


@pytest.mark.parametrize("driver", [ERASynthPlus, Keithley2600, RhodeSchwarzSGS100A, GS200, Cluster, Pulsar, SpiRack])
class TestInstrumentDriverFactoryWithParametrize:
    """Unit test for the Factory of instrument drivers passing parameters"""

    @staticmethod
    def test_handlers(driver: Instrument):
        """Test that the registered handlers are correct"""
        assert InstrumentDriverFactory.handlers[driver.__name__] == driver

    @staticmethod
    def test_get(driver: Instrument):
        """Test that the get method works properly"""
        assert InstrumentDriverFactory.get(name=driver.__name__) == driver


class TestInstrumentDriverFactoryWithoutParametrize:
    """Unit test for the Factory of instrument drivers creating SomeClass"""

    @staticmethod
    def test_handlers():
        """Test that the registered handlers are correct"""
        handlers = InstrumentDriverFactory.handlers

        assert handlers is not None
        assert isinstance(handlers, dict)
        assert len(handlers) > 1

    @staticmethod
    def test_register():
        """Test that the register method works properly with handlers"""
        handlers = InstrumentDriverFactory.handlers

        class SomeClass:
            """Empty class to register and pop"""

        assert SomeClass.__name__ not in handlers

        InstrumentDriverFactory.register(SomeClass)
        assert handlers[SomeClass.__name__] is SomeClass

        handlers.pop(SomeClass.__name__)
        assert SomeClass.__name__ not in handlers

    @staticmethod
    def test_get_instantiate_and_call_methods_of_gotten_class():
        """Test that the get method works properly and that you can use the obtained class"""

        @InstrumentDriverFactory.register
        class SomeClass:
            """Registered class with a method_test to get and call its method"""

            def method_test(self):
                """MethodTest"""
                return "hello world"

        gotten_driver = InstrumentDriverFactory.get(name=SomeClass.__name__)()

        assert gotten_driver is not None
        assert isinstance(gotten_driver, SomeClass)
        assert gotten_driver.method_test() == "hello world"

        InstrumentDriverFactory.handlers.pop(SomeClass.__name__)
