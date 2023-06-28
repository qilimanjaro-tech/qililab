"""SpiRack, D5aDacChannel & S4gDacChannel drivers."""
from qblox_instruments.qcodes_drivers.spi_rack import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules.d5a_module import D5aDacChannel
from qblox_instruments.qcodes_drivers.spi_rack_modules.s4g_module import S4gDacChannel

from qililab.drivers.interfaces import CurrentSource, VoltageSource


class QbloxSpiRack(SpiRack):
    """
    Qililab's driver for the Qblox SpiRack.

    Args:
        name (str): What this instrument is called locally.
        address (str): The GPIB or USB address of this instrument
        kwargs (Any | dict): kwargs to be passed to VisaInstrument class
    """


class QbloxD5aDacChannel(D5aDacChannel, VoltageSource):
    """
    Qililab's driver for the Qblox D5a Module, D5a DAC Channel x16, acting as VoltageSource.

    Args:

    """


class QbloxS4gDacChannel(S4gDacChannel, CurrentSource):
    """
    Qililab's driver for the Qblox S4g Module, S4g DAC Channel x4, acting as CurrentSource.

    Args:

    """
