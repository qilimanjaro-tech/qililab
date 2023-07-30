""" Unit testing module for the Factory of instrument drivers"""
import pytest

from qililab.drivers.instruments import GS200, Cluster, ERASynthPlus, Keithley2600, Pulsar, RhodeSchwarzSGS100A, SpiRack
from qililab.drivers.instruments.instrument_factory import InstrumentDriverFactory


@pytest.mark.parametrize("driver", [ERASynthPlus, Keithley2600, RhodeSchwarzSGS100A, GS200, Cluster, Pulsar, SpiRack])
class TestInstrumentDriverFactoryWithParametrize:
    """Unit test for the Factory of instrument drivers passing parameters"""

    @staticmethod
    def test_handlers(driver):
        """Test that the registered handlers are correct"""
        handlers = InstrumentDriverFactory.handlers

        assert handlers[driver.__name__] == driver
        assert len(handlers) > 1
        assert handlers is not None
        assert isinstance(handlers, dict)

    @staticmethod
    def test_get(driver):
        """Test that the get method works properly"""
        gotten_driver = InstrumentDriverFactory.get(name=driver.__name__)

        assert gotten_driver is not None
        assert gotten_driver == driver


class TestInstrumentDriverFactoryCreatingAnEmptySomeClass:
    """Unit test for the Factory of instrument drivers creating an SomeClass"""

    @staticmethod
    def test_register():
        """Test that the register method works properly with handlers"""

        class SomeClass:
            """Empty class to register and pop"""

        assert SomeClass.__name__ not in InstrumentDriverFactory.handlers
        InstrumentDriverFactory.register(SomeClass)
        assert InstrumentDriverFactory.handlers[SomeClass.__name__] is SomeClass
        InstrumentDriverFactory.handlers.pop(SomeClass.__name__)
        assert SomeClass.__name__ not in InstrumentDriverFactory.handlers

    @staticmethod
    def test_get_instantiate_and_call_gotten_class_methods():
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
