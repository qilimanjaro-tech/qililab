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

import re
from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar

from qililab.instruments.decorators import check_device_initialized
from qililab.runcard.runcard import RuncardInstrument
from qililab.settings.instruments.channel_settings import ChannelSettings
from qililab.settings.instruments.instrument_settings import InstrumentSettings
from qililab.typings.enums import Parameter
from qililab.typings.instruments.device import Device
from qililab.typings.type_aliases import ParameterValue

TDevice = TypeVar("TDevice", bound=Device)
TSettings = TypeVar("TSettings", bound=InstrumentSettings)
TChannelSettings = TypeVar("TChannelSettings", bound=ChannelSettings | None)
TChannelID = TypeVar("TChannelID", bound=int | str | None)


class Instrument2(ABC, Generic[TDevice, TSettings, TChannelSettings, TChannelID]):
    settings: TSettings
    device: TDevice

    _FIELD_AS_LIST_REGEX = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+)]$")

    def __init__(self, settings: TSettings | None = None):
        if settings is None:
            settings = self.get_default_settings()
        self.settings = settings

    @property
    def alias(self):
        """Instrument 'alias' property.

        Returns:
            str: settings.alias.
        """
        return self.settings.alias

    def is_device_active(self) -> bool:
        """Check whether or not the device is currently active.

        Returns:
            bool: Whether or not the device has been initialized.
        """
        return hasattr(self, "device") and self.device is not None

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
    def get_default_settings(cls) -> TSettings:
        pass

    @classmethod
    @abstractmethod
    def parameter_to_instrument_settings(cls) -> dict[Parameter, str]:
        pass

    @classmethod
    @abstractmethod
    def parameter_to_channel_settings(cls) -> dict[Parameter, str]:
        pass

    @abstractmethod
    def get_channel_settings(self, channel: TChannelID) -> TChannelSettings:
        pass

    @abstractmethod
    def parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        pass

    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel: TChannelID):
        if parameter in self.parameter_to_channel_settings():
            if channel is None:
                raise ValueError(f"Channel must be specified for parameter '{parameter.name}'.")
            channel_settings = self.get_channel_settings(channel)
            field_names = self.parameter_to_channel_settings()[parameter]
            for field_name in field_names.split(","):
                match = self._FIELD_AS_LIST_REGEX.match(field_name)
                if match:
                    field_name = match.group(1)
                    index = int(match.group(2))
                    if hasattr(channel_settings, field_name):
                        attr_value = getattr(channel_settings, field_name)
                        if isinstance(attr_value, list) and 0 <= index < len(attr_value):
                            attr_value[index] = value
                            self._execute_set_device_parameter(parameter, value, channel)
                        else:
                            raise ValueError(
                                f"Field '{field_name}' linked with parameter '{parameter.name}' is not a list or index {index} is out of range."
                            )
                    else:
                        raise ValueError(
                            f"Field '{field_name}' linked with parameter {parameter.name} not found in instrument settings."
                        )
                elif hasattr(channel_settings, field_name):
                    setattr(channel_settings, field_name, value)
                    self._execute_set_device_parameter(parameter, value, channel)
                else:
                    raise ValueError(
                        f"Field '{field_name}' linked with parameter {parameter.name} not found in channel settings."
                    )
        elif parameter in self.parameter_to_instrument_settings():
            if channel is not None:
                raise ValueError(f"Channel should not be specified for instrument-wide parameter '{parameter.name}'.")
            field_names = self.parameter_to_instrument_settings()[parameter]
            for field_name in field_names.split(","):
                match = self._FIELD_AS_LIST_REGEX.match(field_name)
                if match:
                    field_name = match.group(1)
                    index = int(match.group(2))
                    if hasattr(self.settings, field_name):
                        attr_value = getattr(self.settings, field_name)
                        if isinstance(attr_value, list) and 0 <= index < len(attr_value):
                            attr_value[index] = value
                            self._execute_set_device_parameter(parameter, value)
                        else:
                            raise ValueError(
                                f"Field '{field_name}' linked with parameter '{parameter.name}' is not a list or index {index} is out of range."
                            )
                    else:
                        raise ValueError(
                            f"Field '{field_name}' linked with parameter {parameter.name} not found in instrument settings."
                        )
                elif hasattr(self.settings, field_name):
                    setattr(self.settings, field_name, value)
                    self._execute_set_device_parameter(parameter, value)
                else:
                    raise ValueError(
                        f"Field '{field_name}' linked with parameter {parameter.name} not found in instrument settings."
                    )
        else:
            raise ValueError(f"Parameter '{parameter.name}' not valid for {self.__class__.__name__}.")

    def _execute_set_device_parameter(
        self, parameter: Parameter, value: ParameterValue, channel: TChannelID | None = None
    ):
        if self.is_device_active():
            operations = self.parameter_to_device_operation()
            if parameter in operations:
                if channel is None:
                    operations[parameter](value)
                else:
                    operations[parameter](value, channel)

    def get_parameter(self, parameter: Parameter, channel: TChannelID):
        if parameter in self.parameter_to_channel_settings():
            if channel is None:
                raise ValueError(f"Channel must be specified for parameter '{parameter.name}'.")
            channel_settings = self.get_channel_settings(channel)
            field_name = self.parameter_to_channel_settings()[parameter]
            if hasattr(channel_settings, field_name):
                return getattr(channel_settings, field_name)
            raise ValueError(f"Field '{field_name}' not found in channel settings.")
        if parameter in self.parameter_to_instrument_settings():
            if channel is not None:
                raise ValueError(f"Channel should not be specified for instrument-wide parameter '{parameter.name}'.")
            field_name = self.parameter_to_instrument_settings()[parameter]
            if hasattr(self.settings, field_name):
                return getattr(self.settings, field_name)
            raise ValueError(f"Field '{field_name}' not found in instrument settings.")
        raise ValueError(f"Parameter '{parameter.name}' not valid for {self.__class__.__name__}.")

    def get_settable_parameters(self) -> list[Parameter]:
        return list(self.parameter_to_instrument_settings().keys()) + list(self.parameter_to_channel_settings().keys())

    @abstractmethod
    def to_runcard(self) -> RuncardInstrument:
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(settings={self.settings})"
