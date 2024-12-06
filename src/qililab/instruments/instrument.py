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
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING, Callable, ClassVar, Generic, Optional

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument_parameter import InstrumentParameter
from qililab.types import TChannelID, TChannelSettings, TDevice, TInstrumentSettings, TInstrumentWithChannelsSettings

if TYPE_CHECKING:
    from qililab.instruments.instrument_type import InstrumentType
    from qililab.runcard.runcard_instruments import RuncardInstrument
    from qililab.settings.instruments.input_settings import InputSettings
    from qililab.settings.instruments.output_settings import OutputSettings
    from qililab.typings.enums import Parameter
    from qililab.typings.type_aliases import ParameterValue


class Instrument(ABC, Generic[TDevice, TInstrumentSettings]):
    device: TDevice
    settings: TInstrumentSettings
    parameters: dict[str, InstrumentParameter]

    def __init__(self, settings: TInstrumentSettings | None = None):
        if settings is None:
            settings = self.get_default_settings()
        self.settings = settings
        self.parameters = {}

    @property
    def alias(self):
        return self.settings.alias

    def is_device_active(self) -> bool:
        """Check whether or not the device is currently active.

        Returns:
            bool: Whether or not the device has been initialized.
        """
        return hasattr(self, "device") and self.device is not None
    
    def add_parameter(self, name: str, setting_key: str, get_driver_cmd: Callable | None = None, set_driver_cmd: Callable | None = None, **kwargs):
        """
        Registers a new QCoDeS parameter for the instrument.

        Parameters:
            name: The name of the parameter.
            setting_key: The key in the settings model corresponding to this parameter.
            **kwargs: Additional arguments for the `InstrumentParameter` class.
        """
        param: InstrumentParameter = InstrumentParameter(
            name=name,
            owner=self,
            setting_key=setting_key,
            get_driver_cmd=get_driver_cmd,
            set_driver_cmd=set_driver_cmd,
            **kwargs,
        )
        self.parameters[name] = param
        setattr(self, name, param)

    @check_device_initialized
    @abstractmethod
    def turn_on(self):
        """Turn on an instrument."""

    @check_device_initialized
    @abstractmethod
    def turn_off(self):
        """Turn off an instrument."""

    @check_device_initialized
    @abstractmethod
    def reset(self):
        """Reset instrument settings."""

    @check_device_initialized
    @abstractmethod
    def initial_setup(self):
        """Set initial instrument settings."""

    @classmethod
    @abstractmethod
    def get_default_settings(cls) -> TInstrumentSettings:
        pass

    @abstractmethod
    def to_runcard(self) -> "RuncardInstrument":
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(settings={self.settings})"
    

class InstrumentWithChannels(
    Instrument[TDevice, TInstrumentWithChannelsSettings], Generic[TDevice, TInstrumentWithChannelsSettings, TChannelSettings, TChannelID]
):
    channels: dict[TChannelID, Channel]

    def __init__(self, settings: TInstrumentWithChannelsSettings | None = None):
        super().__init__(settings=settings)
        self.channels = {}

    def add_channel_parameter(
        self,
        channel_id: TChannelID,
        name: str,
        setting_key: str,
        get_driver_cmd: Callable | None = None,
        set_driver_cmd: Callable | None = None,
        **kwargs,
    ):
        """
        Registers a QCoDeS parameter for a specific channel.

        Parameters:
            channel_id: The ID of the channel.
            name: The name of the parameter.
            setting_key: The key in the channel settings model corresponding to this parameter.
            **kwargs: Additional arguments for the `InstrumentParameter` class.
        """
        if channel_id not in self.channels:
            self.channels[channel_id] = Channel(channel_id)
        
        param = InstrumentParameter(
            name=f"{name}_ch{channel_id}",
            owner=self,
            setting_key=f"{setting_key}",
            channel_id=channel_id,
            get_driver_cmd=get_driver_cmd,
            set_driver_cmd=set_driver_cmd,
            **kwargs,
        )
        # Add the parameter to the channel
        self.channels[channel_id].add_parameter(name, param)

        # Add the channel as an attribute for dot notation access
        setattr(self, f"ch{channel_id}", self.channels[channel_id])


class Channel:
    parameters: dict[str, InstrumentParameter]

    def __init__(self, channel_id: TChannelID):
        self.channel_id = channel_id
        self.parameters = {}

    def add_parameter(self, name: str, parameter: InstrumentParameter):
        """
        Add a QCoDeS parameter to this channel.
        """
        self.parameters[name] = parameter
        setattr(self, name, parameter)
