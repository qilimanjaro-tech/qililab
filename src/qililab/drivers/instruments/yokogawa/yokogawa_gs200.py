"""Yokogawa GS200 driver."""
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qcodes.instrument_drivers.yokogawa.GS200 import GS200 as QCodesGS200
from qcodes.instrument_drivers.yokogawa.GS200 import GS200_Monitor as QCodesGS200Monitor
from qcodes.instrument_drivers.yokogawa.GS200 import GS200Program as QCodesGS200Program

from qililab.drivers.interfaces import CurrentSource, VoltageSource


class GS200(QCodesGS200):
    """
    Qililab's driver for the Yokogawa GS200 acting as VoltageSource and CurrentSource

    Args:
        name (str): What this instrument is called locally.
        address (str): The GPIB or USB address of this instrument
        kwargs (Any | dict): kwargs to be passed to VisaInstrument class
    """

    def __init__(self, name: str, address: str, **kwargs):
        """Initialize the instrument driver."""
        super().__init__(name, address, **kwargs)
        self.submodules: dict[str, InstrumentModule | ChannelTuple] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self.channels: list[QCodesGS200Monitor] = []  # resetting superclass instrument channels
        # Add the Monitor to the instrument
        self.add_submodule("measure", GS200Monitor(self, name="measure", present=True))
        # Add the Program to the instrument
        self.add_submodule("program", QCodesGS200Program(self, name="program"))


class GS200Monitor(QCodesGS200Monitor, VoltageSource, CurrentSource):
    """
    Class for the Yokogawa GS200 Monitor.

    It inherits from QCodes driver.

    Args:
        parent (QCodes.Instrument): The Instrument instance to which the channel is to be attached.
        name (str): The 'colloquial' name of the channel
        present (bool): Monitor is present
    """
