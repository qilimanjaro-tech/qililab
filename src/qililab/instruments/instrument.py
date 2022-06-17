"""Instrument class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Callable, Type, get_type_hints

from qililab.config import logger
from qililab.platform import BusElement
from qililab.settings import Settings
from qililab.typings import Device, InstrumentName, Parameter


class Instrument(BusElement, ABC):
    """Abstract base class declaring the necessary attributes
    and methods for the instruments connected via TCP/IP.

    Args:
        device (Device): Class used for connecting to the instrument.
        settings (Settings): Class containing the settings of the instrument.
    """

    name: InstrumentName

    @dataclass
    class InstrumentSettings(Settings):
        """Contains the settings of an instrument.

        Args:
            ip (str): IP address of the instrument.
        """

        ip: str
        firmware: str

    class CheckConnected:
        """Property used to check if the instrument is connected."""

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
                AttributeError: If the instrument is not connected.
            """
            if not ref._connected or not hasattr(ref, "device"):
                raise AttributeError("Instrument is not connected")
            return self._method(ref, *args, **kwargs)

    settings: InstrumentSettings  # a subtype of settings must be specified by the subclass
    device: Device  # a subtype of device must be specified by the subclass

    def __init__(self, settings: dict):
        """Cast the settings to its corresponding class."""
        settings_class: Type[self.InstrumentSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings)
        self._connected = False

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        logger.info("Connecting to instrument %s.", self.name.value)
        if self._connected:
            raise ValueError("Instrument is already connected")
        self._initialize_device()
        self._connected = True

    def close(self):
        """Close connection with the instrument."""
        if self._connected:
            logger.info("Closing instrument %s.", self.name.value)
            self.stop()
            self.device.close()
            self._connected = False

    def set_parameter(self, parameter: Parameter | str, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        if isinstance(parameter, Parameter):
            parameter = parameter.value
        self.settings.set_parameter(name=parameter, value=value)
        if self._connected:
            self.setup()

    @abstractmethod
    def start_sequencer(self):
        """Start instrument."""

    @abstractmethod
    def setup(self):
        """Set instrument settings."""

    @abstractmethod
    def stop(self):
        """Stop instrument."""

    @abstractmethod
    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    @property
    def id_(self):
        """Instrument 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def category(self):
        """Instrument 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def ip(self):
        """Instrument 'ip' property.

        Returns:
            str: settings.ip.
        """
        return self.settings.ip

    @property
    def firmware(self):
        """Instrument 'firmware' property.

        Returns:
            str: settings.firmware.
        """
        return self.settings.firmware
