"""Unit tests for Keithley_2600"""

from unittest.mock import MagicMock

from qcodes import Instrument
from qcodes.tests.instrument_mocks import DummyChannel, DummyInstrument
from qililab.drivers.instruments.keithley import Keithley2600

class MockKeithley2600(DummyInstrument):
    """Mocking classes for Keithley2600"""

    def __init__(self, name, address, **kwargs):
        """Init method for the mock Keithley2600"""

        super().__init__(name, **kwargs)


class TestKeithley2600:
    """Unit tests checking the qililab Keithley2600 attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_keithley_2600_bases: tuple[type, ...] = Keithley2600.__bases__
        Keithley2600.__bases__ = (MockKeithley2600,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        Keithley2600.__bases__ = cls.old_keithley_2600_bases

    def test_init(self):
        """Unit tests for init method"""

        keithley_2600 = Keithley2600(name="test_spi_rack", address="192.168.1.68")
