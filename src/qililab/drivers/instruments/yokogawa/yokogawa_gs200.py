"""Yokogawa GS200 driver."""
from typing import Any

from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qcodes.instrument_drivers.yokogawa.GS200 import GS200 as QCodesGS200
from qcodes.instrument_drivers.yokogawa.GS200 import GS200_Monitor as QCodesGS200Monitor
from qcodes.instrument_drivers.yokogawa.GS200 import GS200Program as QCodesGS200Program

from qililab.drivers.instruments.instrument_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import BaseInstrument


@InstrumentDriverFactory.register
class GS200(QCodesGS200, BaseInstrument):
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
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass instrument channel lists
        # Add the Monitor to the instrument
        self.add_submodule("measure", QCodesGS200Monitor(self, name="measure", present=True))
        # Add the Program to the instrument
        self.add_submodule("program", QCodesGS200Program(self, name="program"))

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name
