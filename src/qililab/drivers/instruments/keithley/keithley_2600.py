"""Keithley2600 & Keithley2600Channel drivers."""
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qcodes.instrument_drivers.Keithley._Keithley_2600 import Keithley2600 as QCodesKeithley2600
from qcodes.instrument_drivers.Keithley._Keithley_2600 import Keithley2600Channel as QCodesKeithley2600Channel

from qililab.drivers.interfaces import CurrentSource, VoltageSource


class Keithley2600(QCodesKeithley2600):
    """
    This is the driver for the Keithley_2600 Source-Meter series,tested with Keithley_2614B

    Args:
        name (str): Name to use internally in QCoDeS
        address (str): VISA resource address
    """

    def __init__(self, name: str, address: str, **kwargs):
        """Initialize the instrument driver."""
        super().__init__(name, address, **kwargs)
        self.submodules: dict[str, InstrumentModule | ChannelTuple] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self.channels: list[QCodesKeithley2600Channel] = []  # resetting superclass instrument channels
        # Add the channel to the instrument
        for ch in ["a", "b"]:
            ch_name = f"smu{ch}"
            channel = Keithley2600Channel(self, ch_name, ch_name)
            self.add_submodule(ch_name, channel)
            self.channels.append(channel)


class Keithley2600Channel(QCodesKeithley2600Channel, VoltageSource, CurrentSource):
    """
    Class to hold the two Keithley channels, i.e. SMUA and SMUB.

    It inherits from QCodes driver with extra on/off functionalities.

    Args:
        parent (QCodes.Instrument): The Instrument instance to which the channel is to be attached.
        name (str): The 'colloquial' name of the channel
        channel (str): The name used by the Keithley, i.e. either 'smua' or 'smub'
    """

    def on(self) -> None:
        """Turn output on"""
        self.set(param_name="output", value="on")

    def off(self) -> None:
        """Turn output off"""
        self.set(param_name="output", value="off")
