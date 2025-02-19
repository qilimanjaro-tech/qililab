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

"""Instrument class"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import get_type_hints

from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.platform.components.bus_element import BusElement
from qililab.settings import Settings
from qililab.typings import ChannelID, Device, InstrumentName, Parameter, ParameterValue


class Instrument(BusElement, ABC):
    """Abstract base class declaring the necessary attributes
    and methods for the instruments.

    Args:
        settings (Settings): Class containing the settings of the instrument.
    """

    name: InstrumentName

    @dataclass
    class InstrumentSettings(Settings):
        """Contains the settings of an instrument.

        Args:
            alias (str): Alias of the instrument.
        """

        alias: str

    settings: InstrumentSettings  # a subtype of settings must be specified by the subclass
    device: Device

    def is_device_active(self) -> bool:
        """Check wether or not the device is currently active, for instrument childs.

        Contrary to ``CheckDeviceInitialized``, we also check if the device is not None, since a ``disconnect()`` after
        initialization would set it to None.

        Returns:
            bool: Wether or not the device has been initialized.
        """
        return hasattr(self, "device") and self.device is not None

    def __init__(self, settings: dict):
        settings_class: type[Instrument.InstrumentSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings)

    def __str__(self):
        """String representation of an instrument."""
        return f"{self.alias}"

    @property
    def alias(self):
        """Instrument 'alias' property.

        Returns:
            str: settings.alias.
        """
        return self.settings.alias

    def is_awg(self) -> bool:
        """Returns True if instrument is an AWG."""
        return False

    def is_adc(self) -> bool:
        """Returns True if instrument is an ADC."""
        return False

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

    @abstractmethod
    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None) -> ParameterValue:
        """Gets the parameter of a specific instrument.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int, optional): Instrument channel, if multiple. Defaults to None.

        Returns:
            str | int | float | bool: Parameter value.
        """

    @log_set_parameter
    @abstractmethod
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None):
        """Sets the parameter of a specific instrument.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int, optional): instrument channel to update, if multiple. Defaults to None.

        Returns:
            bool: True if the parameter is set correctly, False otherwise
        """


class ParameterNotFound(Exception):
    """Error raised when a parameter in an instrument is not found."""

    def __init__(
        self,
        instrument: Instrument,
        parameter: Parameter,
    ):
        self.message: str = (
            f"Could not find parameter {parameter} in instrument {instrument.name} with alias {instrument.alias}."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"ParameterNotFound: {self.message}"
