"""Keithley2600 driver."""
from qcodes.instrument_drivers.Keithley._Keithley_2600 import Keithley2600 as QCodesKeithley2600


class Keithley2600(QCodesKeithley2600):
    """
    This is the driver for the Keithley_2600 Source-Meter series,tested with Keithley_2614B

    Args:
        name (str): Name to use internally in QCoDeS
        address (str): VISA resource address
    """
