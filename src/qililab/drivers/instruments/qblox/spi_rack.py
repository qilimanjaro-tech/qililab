"""Drivers for SpiRack and its corresponging channels: D5aDacChannel & S4gDacChannel."""
from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules.d5a_module import D5aDacChannel
from qblox_instruments.qcodes_drivers.spi_rack_modules.s4g_module import S4gDacChannel

from qililab.drivers.interfaces import CurrentSource, VoltageSource


class QbloxSpiRack(SpiRack):
    """
    Qililab's driver for the Qblox SpiRack.

    SPI rack driver class based on `QCoDeS <https://qcodes.github.io/Qcodes/>`_.

    Args:
        name (str): Instrument name.
        address (str): COM port used by SPI rack controller unit (e.g. "COM4")
        baud_rate (int): Baud rate. Default to 9600.
        timeout (float): Data receive timeout in seconds. Default to 1.
        is_dummy (bool): If true, the SPI rack driver is operating in "dummy" mode for testing purposes. Default to False.
    """


class QbloxD5aDacChannel(D5aDacChannel, VoltageSource):
    """
    Qililab's driver for the Qblox D5a Module, D5a DAC Channel x16, acting as VoltageSource.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the dac channels of the D5a module.

    Args:
        parent (D5aModule): Reference to the parent :class:`~qblox_instruments.qcodes_drivers.spi_rack_modules.D5aModule`
        name (str): Name for the instrument channel
        dac (int): Number of the dac that this channel corresponds to
    """


class QbloxS4gDacChannel(S4gDacChannel, CurrentSource):
    """
    Qililab's driver for the Qblox S4g Module, S4g DAC Channel x4, acting as CurrentSource.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the dac channels of the S4g module.

    Args:
        parent (D5aModule): Reference to the parent :class:`~qblox_instruments.qcodes_drivers.spi_rack_modules.D5aModule`
        name (str): Name for the instrument channel
        dac (int): Number of the dac that this channel corresponds to
    """
