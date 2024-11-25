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

from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar

from qililab.instruments.decorators import check_device_initialized
from qililab.runcard.runcard import RuncardInstrument
from qililab.settings.instruments.channel_settings import ChannelSettings
from qililab.settings.instruments.input_settings import InputSettings
from qililab.settings.instruments.instrument_settings import InstrumentSettings
from qililab.settings.instruments.output_settings import OutputSettings
from qililab.typings.enums import Parameter
from qililab.typings.instruments.device import Device
from qililab.typings.type_aliases import ParameterValue

TDevice = TypeVar("TDevice", bound=Device)
TSettings = TypeVar("TSettings", bound=InstrumentSettings)
TChannelSettings = TypeVar("TChannelSettings", bound=ChannelSettings | None)
TChannel = TypeVar("TChannel", bound=int | str | None)
TOutputSettings = TypeVar("TOutputSettings", bound=OutputSettings | None)
TInputSettings = TypeVar("TInputSettings", bound=InputSettings | None)


class Instrument2(ABC, Generic[TDevice, TSettings, TChannelSettings, TChannel, TOutputSettings, TInputSettings]):
    settings: TSettings
    device: TDevice

    def __init__(self, settings: TSettings | None = None):
        if settings is None:
            settings = self.get_default_settings()
        self.settings = settings

    @property
    def alias(self):
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
    def _instrument_parameter_to_settings(cls) -> dict[Parameter, str]:
        return {}

    @classmethod
    def _channel_parameter_to_settings(cls) -> dict[Parameter, str]:
        return {}

    @classmethod
    def _output_parameter_to_settings(cls) -> dict[Parameter, str]:
        return {}

    @classmethod
    def _input_parameter_to_settings(cls) -> dict[Parameter, str]:
        return {}

    def get_channel_settings(self, channel: TChannel) -> TChannelSettings | None:
        return None

    def get_output_settings(self, output: int) -> OutputSettings | None:
        return None

    def get_input_settings(self, input: int) -> InputSettings | None:
        return None

    def _instrument_parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return {}

    def _channel_parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return {}

    def _output_parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return {}

    def _input_parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return {}

    def set_parameter(
        self,
        parameter: Parameter,
        value: ParameterValue,
        *,
        channel: TChannel | None = None,
        output: int | None = None,
        input: int | None = None,
    ):
        number_of_specifiers = sum(param is not None for param in [channel, output, input])
        if number_of_specifiers not in {0, 1}:
            raise ValueError("Either none, or exactly one of channel, output, and input must be specified.")
        if parameter in self._instrument_parameter_to_settings() and number_of_specifiers == 0:
            field_name = self._instrument_parameter_to_settings()[parameter]
            if hasattr(self.settings, field_name):
                setattr(self.settings, field_name, value)
                if self.is_device_active() and parameter in self._instrument_parameter_to_device_operation():
                    self._instrument_parameter_to_device_operation()[parameter](value)
            else:
                raise ValueError(
                    f"Field '{field_name}' linked with parameter {parameter.name} not found in instrument settings."
                )
        elif parameter in self._channel_parameter_to_settings() and channel is not None:
            channel_settings = self.get_channel_settings(channel)
            field_name = self._channel_parameter_to_settings()[parameter]
            if hasattr(channel_settings, field_name):
                setattr(channel_settings, field_name, value)
                if self.is_device_active() and parameter in self._channel_parameter_to_device_operation():
                    self._channel_parameter_to_device_operation()[parameter](value, channel)
            else:
                raise ValueError(
                    f"Field '{field_name}' linked with parameter {parameter.name} not found in channel settings."
                )
        elif parameter in self._output_parameter_to_settings() and output is not None:
            output_settings = self.get_output_settings(output)
            field_name = self._output_parameter_to_settings()[parameter]
            if hasattr(output_settings, field_name):
                setattr(output_settings, field_name, value)
                if self.is_device_active() and parameter in self._output_parameter_to_device_operation():
                    self._output_parameter_to_device_operation()[parameter](value, output)
            else:
                raise ValueError(
                    f"Field '{field_name}' linked with parameter {parameter.name} not found in output settings."
                )
        elif parameter in self._input_parameter_to_settings() and input is not None:
            input_settings = self.get_input_settings(input)
            field_name = self._input_parameter_to_settings()[parameter]
            if hasattr(input_settings, field_name):
                setattr(input_settings, field_name, value)
                if self.is_device_active() and parameter in self._input_parameter_to_device_operation():
                    self._input_parameter_to_device_operation()[parameter](value, input)
            else:
                raise ValueError(
                    f"Field '{field_name}' linked with parameter {parameter.name} not found in input settings."
                )
        else:
            raise ValueError(f"Parameter '{parameter.name}' not valid for {self.__class__.__name__}.")

    def get_parameter(
        self,
        parameter: Parameter,
        *,
        channel: TChannel | None = None,
        output: int | None = None,
        input: int | None = None,
    ):
        number_of_specifiers = sum(param is not None for param in [channel, output, input])
        if number_of_specifiers not in {0, 1}:
            raise ValueError("Either none, or exactly one of channel, output, and input must be specified.")
        if parameter in self._instrument_parameter_to_settings() and number_of_specifiers == 0:
            field_name = self._instrument_parameter_to_settings()[parameter]
            if hasattr(self.settings, field_name):
                return getattr(self.settings, field_name)
            raise ValueError(f"Field '{field_name}' not found in instrument settings.")
        if parameter in self._channel_parameter_to_settings() and channel is not None:
            channel_settings = self.get_channel_settings(channel)
            field_name = self._channel_parameter_to_settings()[parameter]
            if hasattr(channel_settings, field_name):
                return getattr(channel_settings, field_name)
            raise ValueError(f"Field '{field_name}' not found in channel settings.")
        if parameter in self._output_parameter_to_settings() and output is not None:
            output_settings = self.get_output_settings(output)
            field_name = self._output_parameter_to_settings()[parameter]
            if hasattr(output_settings, field_name):
                return getattr(output_settings, field_name)
            raise ValueError(f"Field '{field_name}' not found in output settings.")
        if parameter in self._input_parameter_to_settings() and input is not None:
            input_settings = self.get_input_settings(input)
            field_name = self._input_parameter_to_settings()[parameter]
            if hasattr(input_settings, field_name):
                return getattr(input_settings, field_name)
            raise ValueError(f"Field '{field_name}' not found in input settings.")
        raise ValueError(f"Parameter '{parameter.name}' not valid for {self.__class__.__name__}.")

    @classmethod
    def get_instrument_parameters(cls) -> set[Parameter]:
        return set(cls._instrument_parameter_to_settings())

    @classmethod
    def get_channel_parameters(cls) -> set[Parameter]:
        return set(cls._channel_parameter_to_settings())

    @classmethod
    def get_output_parameters(cls) -> set[Parameter]:
        return set(cls._output_parameter_to_settings())

    @classmethod
    def get_input_parameters(cls) -> set[Parameter]:
        return set(cls._input_parameter_to_settings())

    @classmethod
    def get_parameters(cls) -> set[Parameter]:
        return (
            cls.get_instrument_parameters()
            | cls.get_channel_parameters()
            | cls.get_output_parameters()
            | cls.get_input_parameters()
        )

    @abstractmethod
    def to_runcard(self) -> RuncardInstrument:
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(settings={self.settings})"
