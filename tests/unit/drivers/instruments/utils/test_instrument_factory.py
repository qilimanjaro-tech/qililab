""" Unit testing module for the Factory of instrument drivers"""
import pytest
from qcodes.instrument.instrument import Instrument

from qililab.drivers.instruments import GS200, Cluster, ERASynthPlus, Keithley2600, Pulsar, RhodeSchwarzSGS100A, SpiRack
from qililab.drivers.instruments.utils.instrument_factory import InstrumentDriverFactory


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
        assert InstrumentDriverFactory.handlers[driver.__name__] == driver
        assert len(InstrumentDriverFactory.handlers) != 0

    @staticmethod
    def test_register(driver):
        """Test that the register method works properly"""

    @staticmethod
    def test_get(driver):
        """Test that the get method works properly"""
        assert InstrumentDriverFactory.get(name=driver.__name__) == driver
