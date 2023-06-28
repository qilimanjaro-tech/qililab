""" Test classes, Keithley2600 and Keithley2600Channel"""
from unittest.mock import MagicMock

from qililab.drivers import Keithley2600, Keithley2600Channel


# TODO: Improve this test
class TestOnOff:
    """Test On and off methods we implement in qililab that don't exist in QCoDeS."""

    def test_on(self):
        """Test that needs to be improved"""
        parent = MagicMock()

        a_channel = Keithley2600Channel(parent=parent, name="jesus_a", channel="smua")
        b_channel = Keithley2600Channel(parent=parent, name="jesus_b", channel="smub")

        a_channel.on()
        b_channel.on()

        assert a_channel.get(param_name="output") == b_channel.get(param_name="output") == 1

    def test_off(self):
        """Test that needs to be improved"""
        parent = MagicMock()

        a_channel = Keithley2600Channel(parent=parent, name="jesus_a", channel="smua")
        b_channel = Keithley2600Channel(parent=parent, name="jesus_b", channel="smub")

        a_channel.off()
        b_channel.off()

        assert a_channel.get(param_name="output") == b_channel.get(param_name="output") == 0
