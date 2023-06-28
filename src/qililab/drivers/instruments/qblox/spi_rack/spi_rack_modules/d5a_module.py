"""SpiRack/D5aDacChannel driver."""
from qblox_instruments.qcodes_drivers.spi_rack_modules.d5a_module import D5aDacChannel as QBloxD5aDacChannel

from qililab.drivers.interfaces import VoltageSource


class D5aDacChannel(QBloxD5aDacChannel, VoltageSource):
    """
    Qililab's driver for the YokogawaGS200 acting as VoltageSource and CurrentSource

    Args:
        name (str): What this instrument is called locally.
        address (str): The GPIB or USB address of this instrument
        kwargs (Any | dict): kwargs to be passed to VisaInstrument class
    """
