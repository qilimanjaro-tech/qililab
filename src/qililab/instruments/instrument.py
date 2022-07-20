"""Instrument class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Callable, Type, get_type_hints

from qililab.constants import RUNCARD
from qililab.platform.components.bus_element import BusElement
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
        """

        firmware: str

    settings: InstrumentSettings  # a subtype of settings must be specified by the subclass
    device: Device

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
            if not hasattr(ref, "device"):
                raise AttributeError("Instrument Device has not been initialized")
            return self._method(ref, *args, **kwargs)

    def __init__(self, settings: dict):
        """Cast the settings to its corresponding class."""
        settings_class: Type[self.InstrumentSettings] = get_type_hints(self).get(RUNCARD.SETTINGS)  # type: ignore
        self.settings = settings_class(**settings)

    def set_parameter(self, parameter: Parameter, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        self.settings.set_parameter(parameter=parameter, value=value)
        if hasattr(self, "device"):
            self.setup()

    @CheckDeviceInitialized
    @abstractmethod
    def initial_setup(self):
        """Set initial instrument settings."""

    @CheckDeviceInitialized
    @abstractmethod
    def setup(self):
        """Set instrument settings."""

    @CheckDeviceInitialized
    @abstractmethod
    def reset(self):
        """Reset instrument settings."""

    @CheckDeviceInitialized
    @abstractmethod
    def stop(self):
        """Stop an instrument."""

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
