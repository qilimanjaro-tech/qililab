"""Keithley2600 channels driver."""
from qcodes.instrument_drivers.Keithley._Keithley_2600 import Keithley2600Channel as QCodesKeithley2600Channel

from qililab.drivers.interfaces import CurrentSource, VoltageSource


class Keithley2600Channel(QCodesKeithley2600Channel, VoltageSource, CurrentSource):
    """
    Class to hold the two Keithley channels, i.e. SMUA and SMUB.

    Args:
        parent (QCodes.Instrument): The Instrument instance to which the channel is to be attached.
        name (str): The 'colloquial' name of the channel
        channel (str): The name used by the Keithley, i.e. either 'smua' or 'smub'
    """

    def on(self) -> None:
        """Turn output on"""
        self.write("OUTPUT 1")
        self.output = 1

    def off(self) -> None:
        """Turn output off"""
        self.write("OUTPUT 0")
        self.output = 0
