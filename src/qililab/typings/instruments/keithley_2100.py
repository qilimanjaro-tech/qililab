"""Keithley2600 driver."""
from qcodes.instrument_drivers.tektronix.Keithley_2000 import Keithley_2000

from qililab.typings.instruments.device import Device


class Keithley2100Driver(Keithley_2000, Device):
    """Typing class of the QCoDeS driver for the Keithley 2600 instrument."""
