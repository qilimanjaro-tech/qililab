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

"""Keithley2600 & Keithley2600Channel drivers."""
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qcodes.instrument_drivers.Keithley._Keithley_2600 import Keithley2600 as QCodesKeithley2600
from qcodes.instrument_drivers.Keithley._Keithley_2600 import Keithley2600Channel as QCodesKeithley2600Channel

from qililab.drivers.instruments.instrument_driver_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import BaseInstrument, CurrentSource, VoltageSource


@InstrumentDriverFactory.register
class Keithley2600(QCodesKeithley2600, BaseInstrument):
    """
    This is the driver for the Keithley_2600 Source-Meter series,tested with Keithley_2614B

    Args:
        name (str): Name to use internally in QCoDeS
        address (str): VISA resource address
    """

    def __init__(self, name: str, address: str, **kwargs):
        super().__init__(name, address, **kwargs)
        self.submodules: dict[str, InstrumentModule | ChannelTuple] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass instrument channel lists
        self.channels: list[QCodesKeithley2600Channel] = []  # resetting superclass instrument channels
        # Add the channel to the instrument
        for ch in ["a", "b"]:
            ch_name = f"smu{ch}"
            channel = Keithley2600Channel(self, name=ch_name, channel=ch_name)
            self.add_submodule(ch_name, channel)
            self.channels.append(channel)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name


class Keithley2600Channel(QCodesKeithley2600Channel, VoltageSource, CurrentSource):
    """
    Class to hold the two Keithley channels, i.e. SMUA and SMUB.

    It inherits from QCodes driver with extra on/off functionalities.

    Args:
        parent (QCodes.Instrument): The Instrument instance to which the channel is to be attached.
        name (str): The 'colloquial' name of the channel
        channel (str): The name used by the Keithley, i.e. either 'smua' or 'smub'
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
        """Turn output on"""
        self.set(param_name="output", value="on")

    def off(self) -> None:
        """Turn output off"""
        self.set(param_name="output", value="off")
