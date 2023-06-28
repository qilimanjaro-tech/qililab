"""Drivers for SpiRack and its corresponging channels: D5aDacChannel & S4gDacChannel."""
from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules.d5a_module import D5aDacChannel, D5aModule
from qblox_instruments.qcodes_drivers.spi_rack_modules.s4g_module import S4gDacChannel, S4gModule

from qililab.drivers.interfaces import CurrentSource, VoltageSource


# MAIN SpiRack CLASS
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


# MODULE CLASSES that select the channels
class QbloxD5aModule(D5aModule):
    """
    Qililab's driver for the Qblox D5a Module.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the D5a SPI module.

    Args:
        parent(SpiRack): Reference to the :class:`~qblox_instruments.SpiRack` parent object. This is handled by
            the :func:`~qblox_instruments.SpiRack.add_spi_module` function.
        name (str): Name given to the InstrumentChannel.
        address (int): Module number set on the hardware.
        reset_voltages (bool): If True, then reset all voltages to zero and change the span to `range_max_bi`. Default to False.
        dac_names (Optional[List[str]]): List of all the names to use for the dac channels.
            If no list is given or is None, the default name "dac{i}" is used for the i-th dac channel. Defaults to None.
        is_dummy (bool): If true, do not connect to physical hardware, but use a dummy module. Defaults to False.

    Raises:
        ValueError: Length of the dac names list does not match the number of dacs.
    """


class QbloxS4gModule(S4gModule):
    """
    Qililab's driver for the Qblox S4g Module.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the S4g SPI module.

    Args:
        parent(SpiRack): Reference to the :class:`~qblox_instruments.SpiRack` parent object. This is handled by
            the :func:`~qblox_instruments.SpiRack.add_spi_module` function.
        name (str): Name given to the InstrumentChannel.
        address (int): Module number set on the hardware.
        reset_voltages (bool): If True, then reset all voltages to zero and change the span to `range_max_bi`. Default to False.
        dac_names (Optional[List[str]]): List of all the names to use for the dac channels.
            If no list is given or is None, the default name "dac{i}" is used for the i-th dac channel. Defaults to None.
        is_dummy (bool): If true, do not connect to physical hardware, but use a dummy module. Defaults to False.

    Raises:
        ValueError: Length of the dac names list does not match the number of dacs.
    """


# CHANNELS CLASSES that act as the corresponding Voltage/Current sources.
class QbloxD5aDacChannel(D5aDacChannel, VoltageSource):
    """
    Qililab's driver for the Qblox D5a DAC Channel x16, acting as VoltageSource.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the dac channels of the D5a module.

    Args:
        parent (D5aModule): Reference to the parent :class:`~qblox_instruments.qcodes_drivers.spi_rack_modules.D5aModule`
        name (str): Name for the instrument channel
        dac (int): Number of the dac that this channel corresponds to
    """


class QbloxS4gDacChannel(S4gDacChannel, CurrentSource):
    """
    Qililab's driver for the Qblox S4g DAC Channel x4, acting as CurrentSource.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the dac channels of the S4g module.

    Args:
        parent (D5aModule): Reference to the parent :class:`~qblox_instruments.qcodes_drivers.spi_rack_modules.D5aModule`
        name (str): Name for the instrument channel
        dac (int): Number of the dac that this channel corresponds to
    """
