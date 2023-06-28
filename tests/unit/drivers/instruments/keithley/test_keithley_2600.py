""" Test classes, Keithley2600 and Keithley2600Channel"""
from qcodes.instrument.instrument import Instrument

from qililab.drivers import Keithley2600, Keithley2600Channel


# TODO: Improve this test
class TestOnOff:
    """Test On and off methods we implement in qililab that don't exist in QCoDeS."""

    def test_on(self):
        """Test that need to be improved"""
        a = Keithley2600Channel(parent=Instrument, name="jesus", channel="smua")
        b = Keithley2600Channel(parent=Instrument, name="jesus", channel="smub")
        a.on()
        b.on()

        assert a.output == b.output == 1

    def test_off(self):
        """Test that need to be improved"""
        a = Keithley2600Channel(parent=Instrument, name="jesus", channel="smua")
        b = Keithley2600Channel(parent=Instrument, name="jesus", channel="smub")
        a.off()
        b.off()

        assert a.output == b.output == 0
