"""Instrument class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Callable, Type, get_type_hints

from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.platform.components.bus_element import BusElement
from qililab.pulse import PulseBusSchedule
from qililab.result import Result
from qililab.settings import DDBBElement
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
    class InstrumentSettings(DDBBElement):
        """Contains the settings of an instrument.

        Args:
            firmware (str): Firmware version installed on the instrument.
            channels (int | None): Number of channels supported or None otherwise.
        """

        firmware: str

    settings: InstrumentSettings  # a subtype of settings must be specified by the subclass
    device: Device

    class CheckParameterValueString:
        """Property used to check if the set parameter value is a string."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "Instrument", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                ValueError: If value is neither a float or int.
            """
            if "value" not in kwargs:
                raise ValueError("'value' not specified to update instrument settings.")
            value = kwargs["value"]
            if not isinstance(value, str):
                raise ValueError(f"value must be a string. Current type: {type(value)}")
            return self._method(ref, *args, **kwargs)

    class CheckParameterValueBool:
        """Property used to check if the set parameter value is a bool."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "Instrument", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                ValueError: If value is neither a float or int.
            """
            if "value" not in kwargs:
                raise ValueError("'value' not specified to update instrument settings.")
            value = kwargs["value"]
            if not isinstance(value, bool):
                raise ValueError(f"value must be a bool. Current type: {type(value)}")
            return self._method(ref, *args, **kwargs)

    class CheckParameterValueFloatOrInt:
        """Property used to check if the set parameter value is a float or int."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "Instrument", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                ValueError: If value is neither a float or int.
            """
            if "value" not in kwargs:
                raise ValueError("'value' not specified to update instrument settings.")
            value = kwargs["value"]
            if not isinstance(value, float) and not isinstance(value, int):
                raise ValueError(f"value must be a float or an int. Current type: {type(value)}")
            if isinstance(value, int):
                # setting a float as type as expected
                kwargs["value"] = float(value)
            return self._method(ref, *args, **kwargs)

    class CheckDeviceInitialized:
        """Property used to check if the device has been initialized."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "Instrument", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                AttributeError: If device has not been initialized.
            """
            if not hasattr(ref, "device") and (not args or not hasattr(args[0], "device")):
                raise AttributeError("Instrument Device has not been initialized")
            return self._method(ref, *args, **kwargs) if hasattr(ref, "device") else self._method(*args, **kwargs)

    def __init__(self, settings: dict):
        """Cast the settings to its corresponding class."""
        settings_class: Type[self.InstrumentSettings] = get_type_hints(self).get(RUNCARD.SETTINGS)  # type: ignore
        self.settings = settings_class(**settings)

    @CheckDeviceInitialized
    @abstractmethod
    def initial_setup(self):
        """Set initial instrument settings."""

    @CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float | str | bool): new value
            channel_id (int | None): channel identifier of the parameter to update
        """
        raise ParameterNotFound(f"Could not find parameter {parameter} in instrument {self.name}")

    @CheckDeviceInitialized
    @abstractmethod
    def turn_on(self):
        """Turn on an instrument."""

    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int
    ) -> None:
        """Generate program to execute and upload it to the instrument.

        In some cases this method might do nothing."""

    def run(self) -> None:
        """Run the sequence previously uploaded to the instrument.

        In some cases this method might do nothing."""

    def acquire_result(self) -> Result | None:
        """Acquire results of the measurement.

        In some cases this method might do nothing."""

    @CheckDeviceInitialized
    @abstractmethod
    def reset(self):
        """Reset instrument settings."""

    @CheckDeviceInitialized
    @abstractmethod
    def turn_off(self):
        """Turn off an instrument."""

    @property
    def id_(self):
        """Instrument 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def alias(self):
        """Instrument 'alias' property.

        Returns:
            str: settings.alias.
        """
        return self.settings.alias

    @property
    def category(self):
        """Instrument 'category' property.

        Returns:
            Category: settings.category.
        """
        return self.settings.category

    @property
    def firmware(self):
        """Instrument 'firmware' property.

        Returns:
            str: settings.firmware.
        """
        return self.settings.firmware

    def __str__(self):
        """String representation of an instrument."""
        return f"{self.alias}" if self.alias is not None else f"{self.category}_{self.id_}"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Sets the parameter of a specific instrument.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.

        Returns:
            bool: True if the parameter is set correctly, False otherwise
        """
        if not hasattr(self, "device"):
            raise ValueError(
                f"Instrument is not connected and cannot set the new value: {value} to the parameter {parameter.value}."
            )
        if channel_id is None:
            logger.debug("Setting parameter: %s to value: %f", parameter.value, value)
        if channel_id is not None:
            logger.debug("Setting parameter: %s to value: %f in channel %d", parameter.value, value, channel_id)

        return self.setup(parameter=parameter, value=value, channel_id=channel_id)


class ParameterNotFound(Exception):
    """Error raised when a parameter in an instrument is not found."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"ParameterNotFound: {self.message}"
