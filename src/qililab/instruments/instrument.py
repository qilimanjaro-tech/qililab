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
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import cast, get_type_hints

from qililab.config.config import logger
from qililab.exceptions import ParameterNotFound
from qililab.instruments.decorators import check_device_initialized
from qililab.platform.components.bus_element import BusElement
from qililab.settings.settings import Settings
from qililab.typings.enums import InstrumentName, Parameter
from qililab.typings.instruments.device import Device


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

    def is_awg(self) -> bool:
        """Returns True if instrument is an AWG."""
        from qililab.instruments.awg import AWG  # pylint: disable=import-outside-toplevel, cyclic-import

        return isinstance(self, AWG)

    def as_awg(self):
        """Cast instrument to AWG."""
        from qililab.instruments.awg import AWG  # pylint: disable=import-outside-toplevel, cyclic-import

        return cast(AWG, self)

    def is_adc(self) -> bool:
        """Returns True if instrument is an AWG/ADC."""
        from qililab.instruments.awg_analog_digital_converter import (  # pylint: disable=import-outside-toplevel, cyclic-import
            AWGAnalogDigitalConverter,
        )

        return isinstance(self, AWGAnalogDigitalConverter)

    def as_adc(self):
        """Cast instrument to AWG/ADC."""
        from qililab.instruments.awg_analog_digital_converter import (  # pylint: disable=import-outside-toplevel, cyclic-import
            AWGAnalogDigitalConverter,
        )

        return cast(AWGAnalogDigitalConverter, self)

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

    @property
    def alias(self):
        """Instrument 'alias' property.

        Returns:
            str: settings.alias.
        """
        return self.settings.alias

    def __str__(self):
        """String representation of an instrument."""
        return f"{self.alias}"

    @check_device_initialized
    @abstractmethod
    def initial_setup(self):
        """Set initial instrument settings."""

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

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | str | None = None):
        """Sets the parameter of a specific instrument.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.

        Returns:
            bool: True if the parameter is set correctly, False otherwise
        """
        if channel_id is None:
            logger.debug("Setting parameter: %s to value: %f", parameter.value, value)
        if channel_id is not None:
            logger.debug("Setting parameter: %s to value: %f in channel %d", parameter.value, value, channel_id)

        return self.setup(parameter=parameter, value=value, channel_id=channel_id)

    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | str | None = None):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float | str | bool): new value
            channel_id (int | None): channel identifier of the parameter to update
        """
        raise ParameterNotFound(f"Could not find parameter {parameter} in instrument {self.name}")

    def get_parameter(self, parameter: Parameter, channel_id: int | str | None = None):
        """Gets the parameter of a specific instrument.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None, optional): Instrument channel, if multiple. Defaults to None.

        Returns:
            str | int | float | bool: Parameter value.
        """
        return self.get(parameter=parameter, channel_id=channel_id)

    def get(self, parameter: Parameter, channel_id: int | str | None = None):  # pylint: disable=unused-argument
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier of the parameter to update.
        """
        if hasattr(self.settings, parameter.value):
            return getattr(self.settings, parameter.value)
        raise ParameterNotFound(f"Could not find parameter {parameter} in instrument {self.name}")
