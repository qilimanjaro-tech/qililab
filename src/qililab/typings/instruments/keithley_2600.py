"""Keithley2600 driver."""
from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import (
    Keithley_2600,
    KeithleyChannel,
)

from qililab.typings import Device


class Keithley2600Driver(Keithley_2600, Device):
    """Typing class of the QCoDeS driver for the Keithley 2600 instrument."""

    smua: KeithleyChannel
    smub: KeithleyChannel
