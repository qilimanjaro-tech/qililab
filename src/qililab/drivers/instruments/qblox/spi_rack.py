"""Drivers for SpiRack and its corresponging channels: D5aDacChannel & S4gDacChannel."""
from typing import Optional

from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules.d5a_module import D5aDacChannel, D5aModule
from qblox_instruments.qcodes_drivers.spi_rack_modules.s4g_module import S4gDacChannel, S4gModule

from qililab.drivers.interfaces import CurrentSource, VoltageSource


# MAIN SpiRack CLASS
class QbloxSpiRack(SpiRack):
    """
    Qililab's driver for the Qblox SpiRack.

    SPI rack driver class based on `QCoDeS <https://qcodes.github.io/Qcodes/>`_.
    """

    def __init__(
        self,
        name: str,
        address: str,
        baud_rate: int = 9600,
        timeout: float = 1,
        is_dummy: bool = False,
    ):
        """
        Initialize the class, as in Qblox but changing the references to qililab classes instead.

        Args:
            name (str): Instrument name.
            address (str): COM port used by SPI rack controller unit (e.g. "COM4")
            baud_rate (int): Baud rate. Default to 9600.
            timeout (float): Data receive timeout in seconds. Default to 1.
            is_dummy (bool): If true, the SPI rack driver is operating in "dummy" mode for testing purposes. Default to False.
        """
        super().__init__(
            name,
            address,
            baud_rate,
            timeout,
            is_dummy,
        )

        self._MODULES_MAP["S4g"] = QbloxS4gModule
        self._MODULES_MAP["D5a"] = QbloxD5aModule
        # TODO: Finish this with the corresponding logic to call Qililab Modules instead than Qblox


# MODULE CLASSES that select the channels
class QbloxD5aModule(D5aModule):
    """
    Qililab's driver for the Qblox D5a Module.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the D5a SPI module.
    """

    def __init__(
        self,
        parent,
        name: str,
        address: int,
        reset_currents: bool = False,
        dac_names: Optional[list[str]] = None,
        is_dummy: bool = False,
    ):
        """
        Args:
            parent(SpiRack): Reference to the :class:`~qblox_instruments.SpiRack` parent object. This is handled by
                the :func:`~qblox_instruments.SpiRack.add_spi_module` function.
            name (str): Name given to the InstrumentChannel.
            address (int): Module number set on the hardware.
            reset_voltages (bool): If True, then reset all voltages to zero and change the span to `range_max_bi`. Default to False.
            dac_names (Optional[List[str]]): List of all the names to use for the dac channels.
                If no list is given or is None, the default name "dac{i}" is used for the i-th dac channel. Defaults to None.
            is_dummy (bool): If true, do not connect to physical hardware, but use a dummy module. Defaults to False.

        Raises: ValueError: Length of the dac names list does not match the number of dacs.
            is_dummy (bool, optional): _description_. Defaults to False.
        """
        super().__init__(parent, name, address, reset_currents, dac_names, is_dummy)

        for dac, old_channel in enumerate(self._channels):
            new_channel = QbloxD5aDacChannel(self, old_channel._chan_name, dac)
            self._channels[dac] = new_channel
            self.add_submodule(old_channel._chan_name, new_channel)
        # TODO: Same here, I wrote this lines very fast. Finish this with the corresponding logic to use Qililab classes instead than Qblox


class QbloxS4gModule(S4gModule):
    """
    Qililab's driver for the Qblox S4g Module.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the S4g SPI module.
    """

    def __init__(
        self,
        parent,
        name: str,
        address: int,
        reset_currents: bool = False,
        dac_names: Optional[list[str]] = None,
        is_dummy: bool = False,
    ):
        """
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
        super().__init__(parent, name, address, reset_currents, dac_names, is_dummy)

        for dac, old_channel in enumerate(self._channels):
            new_channel = QbloxS4gDacChannel(self, old_channel._chan_name, dac)
            self._channels[dac] = new_channel
            self.add_submodule(old_channel._chan_name, new_channel)
        # TODO: Same here, I wrote this lines very fast. Finish this with the corresponding logic to use Qililab classes instead than Qblox


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

    # TODO: This methods are copied from the other file, need to be changed to the correct ones for this case.
    def on(self) -> None:
        """Turn output on"""
        self.set(param_name="output", value=1)

    def off(self) -> None:
        """Turn output off"""
        self.set(param_name="output", value=0)


class QbloxS4gDacChannel(S4gDacChannel, CurrentSource):
    """
    Qililab's driver for the Qblox S4g DAC Channel x4, acting as CurrentSource.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the dac channels of the S4g module.

    Args:
        parent (S4gModule): Reference to the parent :class:`~qblox_instruments.qcodes_drivers.spi_rack_modules.S4gModule`
        name (str): Name for the instrument channel
        dac (int): Number of the dac that this channel corresponds to
    """

    # TODO: This methods are copied from the other file, need to be changed to the correct ones for this case.
    def on(self) -> None:
        """Turn output on"""
        self.set(param_name="output", value=1)

    def off(self) -> None:
        """Turn output off"""
        self.set(param_name="output", value=0)
