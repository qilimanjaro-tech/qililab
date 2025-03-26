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
from typing import TYPE_CHECKING, Callable, Generic

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument_parameter import InstrumentParameter
from qililab.types import TChannelID, TChannelSettings, TDevice, TInstrumentSettings, TInstrumentWithChannelsSettings

if TYPE_CHECKING:
    from qililab.runcard.runcard_instruments import RuncardInstrument


class Instrument(ABC, Generic[TDevice, TInstrumentSettings]):
    """
    Instance for an instrument.

    Parameters:
        device: The type associated to the instrument.
        settings: The settings associated to the instrument.
        parameters: The parameters associated to the instrument.
    """

    device: TDevice
    settings: TInstrumentSettings
    parameters: dict[str, InstrumentParameter]

    def __init__(self, settings: TInstrumentSettings | None = None):
        if settings is None:
            settings = self.get_default_settings()
        self.settings = settings
        self.parameters = {}
        self.outputs = {}
        self.inputs = {}

    @property
    def alias(self):
        """Check instrument alias.

        Returns:
            str: Instrument alias.
        """
        return self.settings.alias

    def is_device_active(self) -> bool:
        """Check whether or not the device is currently active.

        Returns:
            bool: Whether or not the device has been initialized.
        """
        return hasattr(self, "device") and self.device is not None

    def add_output_parameter(
        self,
        output_id: int,
        name: str,
        settings_field: str,
        get_device_value: Callable | None = None,
        set_device_value: Callable | None = None,
        **kwargs,
    ):
        """
        Registers a QCoDeS parameter for a specific output.

        Parameters:
            output_id: The port of the output.
            name: The name of the parameter.
            settings_field: The key in the output settings model corresponding to this parameter.
            get_device_value: Optional callable to retrieve the value from the device.
            set_device_value: Optional callable to set the value in the device.
            **kwargs: Additional arguments for the `InstrumentParameter` class.
        """
        if output_id not in self.outputs:
            self.outputs[output_id] = Output(output_id)

        output_name = f"ch{output_id}"

        param = InstrumentParameter(
            name=f"{name}_{output_name}",
            owner=self,
            settings_field=f"{settings_field}",
            channel_id=output_id,
            get_device_value=get_device_value,
            set_device_value=set_device_value,
            **kwargs,
        )
        # Add the parameter to the output
        self.outputs[output_id].add_parameter(name, param)

        # Add the output as an attribute for dot notation access
        setattr(self, output_name, self.outputs[output_id])

    def add_input_parameter(
        self,
        input_id: int,
        name: str,
        settings_field: str,
        get_device_value: Callable | None = None,
        set_device_value: Callable | None = None,
        **kwargs,
    ):
        """
        Registers a QCoDeS parameter for a specific input.

        Parameters:
            input_id: The port of the input.
            name: The name of the parameter.
            settings_field: The key in the output settings model corresponding to this parameter.
            get_device_value: Optional callable to retrieve the value from the device.
            set_device_value: Optional callable to set the value in the device.
            **kwargs: Additional arguments for the `InstrumentParameter` class.
        """
        if input_id not in self.inputs:
            self.inputs[input_id] = Input(input_id)

        input_name = f"ch{input_id}"

        param = InstrumentParameter(
            name=f"{name}_{input_name}",
            owner=self,
            settings_field=f"{settings_field}",
            channel_id=input_id,
            get_device_value=get_device_value,
            set_device_value=set_device_value,
            **kwargs,
        )
        # Add the parameter to the output
        self.inputs[input_id].add_parameter(name, param)

        # Add the output as an attribute for dot notation access
        setattr(self, input_name, self.inputs[input_id])

    def add_parameter(
        self,
        name: str,
        settings_field: str,
        get_device_value: Callable | None = None,
        set_device_value: Callable | None = None,
        **kwargs,
    ):
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
            settings_field=settings_field,
            get_device_value=get_device_value,
            set_device_value=set_device_value,
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
        """Get default settings."""

    @abstractmethod
    def to_runcard(self) -> "RuncardInstrument":
        """Add instrument to runcard."""

    def __repr__(self):
        return f"{self.__class__.__name__}(settings={self.settings})"


class Output:
    """
    Class for output parameters.

    Parameters:
        parameters: Dictionary with the output parameters string and associated parameters.
    """

    parameters: dict[str, InstrumentParameter]

    def __init__(self, output_id: int):
        self.output_id = output_id
        self.parameters = {}

    def add_parameter(self, name: str, parameter: InstrumentParameter):
        """
        Add a QCoDeS parameter to this output.
        """
        self.parameters[name] = parameter
        setattr(self, name, parameter)


class Input:
    """
    Class for input parameters.

    Parameters:
        parameters: Dictionary with the input parameters string and associated parameters.
    """

    parameters: dict[str, InstrumentParameter]

    def __init__(self, input_id: int):
        self.input_id = input_id
        self.parameters = {}

    def add_parameter(self, name: str, parameter: InstrumentParameter):
        """
        Add a QCoDeS parameter to this input.
        """
        self.parameters[name] = parameter
        setattr(self, name, parameter)


class InstrumentWithChannels(
    Instrument[TDevice, TInstrumentWithChannelsSettings],
    Generic[TDevice, TInstrumentWithChannelsSettings, TChannelSettings, TChannelID],
):
    """
    Instance for an instrument with channels.

    Parameters:
        settings: The settings associated to the instrument.
    """

    channels: dict[TChannelID, Channel]

    def __init__(self, settings: TInstrumentWithChannelsSettings | None = None):
        super().__init__(settings=settings)
        self.channels = {}

    def add_channel_parameter(
        self,
        channel_id: TChannelID,
        name: str,
        settings_field: str,
        get_device_value: Callable | None = None,
        set_device_value: Callable | None = None,
        **kwargs,
    ):
        """
        Registers a QCoDeS parameter for a specific channel.

        Parameters:
            channel_id: The ID of the channel.
            name: The name of the parameter.
            settings_field: The key in the channel settings model corresponding to this parameter.
            get_device_value: Optional callable to retrieve the value from the device.
            set_device_value: Optional callable to set the value in the device.
            **kwargs: Additional arguments for the `InstrumentParameter` class.
        """
        if channel_id not in self.channels:
            self.channels[channel_id] = Channel(channel_id)

        channel_name = f"ch{channel_id}" if isinstance(channel_id, int) else f"{channel_id}"

        param = InstrumentParameter(
            name=f"{name}_{channel_name}",
            owner=self,
            settings_field=f"{settings_field}",
            channel_id=channel_id,
            get_device_value=get_device_value,
            set_device_value=set_device_value,
            **kwargs,
        )
        # Add the parameter to the channel
        self.channels[channel_id].add_parameter(name, param)

        # Add the channel as an attribute for dot notation access
        setattr(self, channel_name, self.channels[channel_id])


class Channel:
    """
    Class to wrap channel parameters.

    Parameters:
        channel_id: The ID of the channel.
    """

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
