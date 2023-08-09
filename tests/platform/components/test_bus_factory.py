""" Unit testing module for the Factory of Buses"""
import pytest

from qililab.platform.components import BusFactory, DriveBus, FluxBus, ReadoutBus
from qililab.platform.components.bus_driver import BusDriver


@pytest.mark.parametrize("bus", [ReadoutBus, FluxBus, DriveBus])
class BusFactoryWithParametrize:
    """Unit test for the Factory of Buses passing parameters"""

    @staticmethod
    def test_handlers(bus: BusDriver):
        """Test that the registered handlers are correct"""
        assert BusFactory.handlers[bus.__name__] == bus

    @staticmethod
    def test_get(bus: BusDriver):
        """Test that the get method works properly"""
        assert BusFactory.get(name=bus.__name__) == bus


class TestBusFactoryWithoutParametrize:
    """Unit test for the Factory of Buses creating SomeClass"""

    @staticmethod
    def test_handlers():
        """Test that the registered handlers are correct"""
        handlers = BusFactory.handlers

        assert handlers is not None
        assert isinstance(handlers, dict)
        assert len(handlers) > 1

    @staticmethod
    def test_register():
        """Test that the register method works properly with handlers"""
        handlers = BusFactory.handlers

        class SomeClass:
            """Empty class to register and pop"""

        assert SomeClass.__name__ not in handlers

        BusFactory.register(SomeClass)
        assert handlers[SomeClass.__name__] is SomeClass

        handlers.pop(SomeClass.__name__)
        assert SomeClass.__name__ not in handlers

    @staticmethod
    def test_get_instantiate_and_call_methods_of_gotten_class():
        """Test that the get method works properly and that you can use the obtained class"""

        @BusFactory.register
        class SomeClass:
            """Registered class with a method_test to get and call its method"""

            def method_test(self):
                """MethodTest"""
                return "hello world"

        gotten_driver = BusFactory.get(name=SomeClass.__name__)()

        assert gotten_driver is not None
        assert isinstance(gotten_driver, SomeClass)
        assert gotten_driver.method_test() == "hello world"

        BusFactory.handlers.pop(SomeClass.__name__)
