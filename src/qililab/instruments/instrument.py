"""Instrument class"""
from abc import ABC, abstractmethod


class Instrument(ABC):
    """Abstract base class declaring the necessary attributes
    and methods for the instruments connected via TCP/IP.

    Args:
        ip (str): IP address of the instrument.
    """

    def __init__(self) -> None:
        self._connected: bool = False

    @abstractmethod
    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""

    @abstractmethod
    def start(self):
        """Start instrument."""

    @abstractmethod
    def stop(self):
        """Stop instrument."""

    @abstractmethod
    def close(self):
        """Close connection with the instrument. Set instrument values to idle values if required."""
