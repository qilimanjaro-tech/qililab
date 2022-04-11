"""Instrument class"""
from abc import ABC, abstractmethod
from typing import Callable

from qililab.constants import INSTRUMENT_TYPES


class Instrument(ABC):
    """Abstract base class declaring the necessary attributes
    and methods for the instruments connected via TCP/IP.

    Args:
        name (str): Name of the instrument.
    """

    class CheckConnected:
        """Property used to check if the instrument is connected."""

        def __init__(self, method: Callable):
            self._method = method

        def __call__(self, ref: "Instrument", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                AttributeError: If the instrument is not connected.
            """
            if not ref._connected or ref.device is None:
                raise AttributeError("Instrument is not connected")
            return self._method(*args, **kwargs)

    def __init__(self, name: str):
        self.name = name
        self.device: INSTRUMENT_TYPES | None = None
        self._connected: bool = False

    @abstractmethod
    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""

    @abstractmethod
    @CheckConnected
    def start(self):
        """Start instrument."""

    @abstractmethod
    @CheckConnected
    def setup(self):
        """Set instrument settings."""

    @abstractmethod
    @CheckConnected
    def stop(self):
        """Stop instrument."""

    @CheckConnected
    def close(self):
        """Close connection with the instrument."""
        self.stop()
        self.device.close()
        self._connected = False
