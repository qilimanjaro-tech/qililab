""" Unit testing module for the Factory of instrument drivers"""
import pytest
from qcodes.instrument.instrument import Instrument

from qililab.drivers.instruments import GS200, Cluster, ERASynthPlus, Keithley2600, Pulsar, RhodeSchwarzSGS100A, SpiRack
from qililab.drivers.instruments.instrument_factory import InstrumentDriverFactory


@pytest.fixture(
    name="driver", params=[ERASynthPlus, Keithley2600, RhodeSchwarzSGS100A, GS200, Cluster, Pulsar, SpiRack]
)
def fixture_driver(request: pytest.FixtureRequest) -> Instrument:
    """Return a Driver object."""
    return request.param  # type: ignore


class TestInstrumentDriverFactory:
    """Unit test for the Factory of instrument drivers"""

    @staticmethod
    def test_handlers(driver):
        """Test that the registered handlers are correct"""
        handlers = InstrumentDriverFactory.handlers

        assert handlers[driver.__name__] == driver
        assert len(handlers) > 1
        assert handlers is not None
        assert isinstance(handlers, dict)

    @staticmethod
    def test_register(driver):
        """Test that the register method works properly"""
        # TODO: Think if this test needs to be here, or if the test of handlers is enough

    @staticmethod
    def test_get(driver):
        """Test that the get method works properly"""
        gotten_driver = InstrumentDriverFactory.get(name=driver.__name__)

        assert gotten_driver == driver
        assert gotten_driver is not None
