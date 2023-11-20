# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Drivers for SpiRack and its corresponging channels: D5aDacChannel & S4gDacChannel."""
from typing import Union

from qblox_instruments import SpiRack as QcodesSpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules.d5a_module import D5aDacChannel as QcodesD5aDacChannel
from qblox_instruments.qcodes_drivers.spi_rack_modules.d5a_module import D5aModule as QcodesD5aModule
from qblox_instruments.qcodes_drivers.spi_rack_modules.s4g_module import S4gDacChannel as QcodesS4gDacChannel
from qblox_instruments.qcodes_drivers.spi_rack_modules.s4g_module import S4gModule as QcodesS4gModule
from qcodes import Instrument
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from qililab.drivers.instruments.instrument_driver_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import BaseInstrument, CurrentSource, VoltageSource


# MAIN SpiRack CLASS
@InstrumentDriverFactory.register
class SpiRack(QcodesSpiRack, BaseInstrument):  # pylint: disable=abstract-method
    """
    Qililab's driver for the Qblox SpiRack.

    SPI rack driver class based on `QCoDeS <https://qcodes.github.io/Qcodes/>`_.

    This class is initialize as in Qblox but changing the references to qililab classes instead.

    Args:
        name (str): Instrument name.
        address (str): COM port used by SPI rack controller unit (e.g. "COM4")
    """

    def __init__(self, name: str, address: str, **kwargs):
        super().__init__(name, address, **kwargs)

        self._MODULES_MAP["S4g"] = S4gModule
        self._MODULES_MAP["D5a"] = D5aModule

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name


# MODULE CLASSES that select the channels
class D5aModule(QcodesD5aModule, BaseInstrument):
    """
    Qililab's driver for the Qblox D5a Module.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the D5a SPI module.

    Args:
        parent(SpiRack): Reference to the :class:`~qblox_instruments.SpiRack` parent object. This is handled by
            the :func:`~qblox_instruments.SpiRack.add_spi_module` function.
        name (str): Name given to the InstrumentChannel.
        address (int): Module number set on the hardware.
    Raises: ValueError: Length of the dac names list does not match the number of dacs.
        is_dummy (bool, optional): _description_. Defaults to False.
    """

    def __init__(self, parent: Instrument, name: str, address: int, **kwargs):
        super().__init__(parent, name, address, **kwargs)

        self.submodules: dict[str, Union[InstrumentModule, ChannelTuple]] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        for dac, old_channel in enumerate(self._channels):
            new_channel = D5aDacChannel(self, old_channel._chan_name, dac)
            self._channels[dac] = new_channel
            self.add_submodule(old_channel._chan_name, new_channel)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name


class S4gModule(QcodesS4gModule, BaseInstrument):
    """
    Qililab's driver for the Qblox S4g Module.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the S4g SPI module.

    Args:
        parent(SpiRack): Reference to the :class:`~qblox_instruments.SpiRack` parent object. This is handled by
            the :func:`~qblox_instruments.SpiRack.add_spi_module` function.
        name (str): Name given to the InstrumentChannel.
        address (int): Module number set on the hardware.

    Raises:
        ValueError: Length of the dac names list does not match the number of dacs.
    """

    def __init__(self, parent: Instrument, name: str, address: int, **kwargs):
        super().__init__(parent, name, address, **kwargs)

        self.submodules: dict[str, Union[InstrumentModule, ChannelTuple]] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        for dac, old_channel in enumerate(self._channels):
            new_channel = S4gDacChannel(self, old_channel._chan_name, dac)
            self._channels[dac] = new_channel
            self.add_submodule(old_channel._chan_name, new_channel)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name


# CHANNELS CLASSES that act as the corresponding Voltage/Current sources.
class D5aDacChannel(QcodesD5aDacChannel, VoltageSource):
    """
    Qililab's driver for the Qblox D5a DAC Channel x16, acting as VoltageSource.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the dac channels of the D5a module.

    Args:
        parent (D5aModule): Reference to the parent :class:`~qblox_instruments.qcodes_drivers.spi_rack_modules.D5aModule`
        name (str): Name for the instrument channel
        dac (int): Number of the dac that this channel corresponds to
    """

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name

    def on(self) -> None:
        """Start D5aDacChannel"""

    def off(self) -> None:
        """Turn output off"""
        self.set(param_name="voltage", value=0)


class S4gDacChannel(QcodesS4gDacChannel, CurrentSource):
    """
    Qililab's driver for the Qblox S4g DAC Channel x4, acting as CurrentSource.

    `QCoDeS <https://qcodes.github.io/Qcodes/>`_ style instrument channel driver for the dac channels of the S4g module.

    Args:
        parent (S4gModule): Reference to the parent :class:`~qblox_instruments.qcodes_drivers.spi_rack_modules.S4gModule`
        name (str): Name for the instrument channel
        dac (int): Number of the dac that this channel corresponds to
    """

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name

    def on(self) -> None:
        """Start S4gDacChannel"""

    def off(self) -> None:
        """Turn output off"""
        self.set(param_name="current", value=0)
