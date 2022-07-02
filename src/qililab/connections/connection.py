"""Instrument class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Callable, Type, get_type_hints

from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.settings import DDBBElement
from qililab.typings import Device


class Connection(ABC):
    """Abstract base class declaring the necessary attributes and methods for a connection."""

    @dataclass
    class ConnectionSettings(DDBBElement):
        """Contains the settings of a connection.

        Args:
            address (str): Connection address of the connected device.
        """

        address: str

    settings: ConnectionSettings  # a subtype of settings must be specified by the subclass
    device: Device  # a subtype of device must be specified by the subclass

    class CheckConnected:
        """Property used to check if the connection has established with an instrument."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "Connection", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                AttributeError: If connection has not been established with an instrument.
            """
            if not ref._connected or not hasattr(ref, "device"):
                raise AttributeError("Instrument is not connected")
            return self._method(ref, *args, **kwargs)

    def __init__(self, settings: dict):
        settings_class: Type[self.ConnectionSettings] = get_type_hints(RUNCARD.SETTINGS)  # type: ignore
        self.settings = settings_class(**settings)
        self._connected = False

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        logger.info("Connecting to instrument %s.", self._device_name())
        if self._connected:
            raise ValueError("Instrument is already connected")
        self._initialize_device()
        self._connected = True

    def close(self):
        """Close connection with the instrument."""
        if self._connected:
            logger.info("Closing instrument %s.", self._device_name())
            self.stop()
            self.device.close()
            self._connected = False

    @abstractmethod
    def _device_name(self) -> str:
        """Gets the device Instrument name."""

    @abstractmethod
    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    @property
    def address(self):
        """Connection 'address' property.

        Returns:
            str: settings.address.
        """
        return self.settings.address
