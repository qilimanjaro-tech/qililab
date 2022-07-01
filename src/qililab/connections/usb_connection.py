"""USBConnection class"""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.connections.connection import Connection


class USBConnection(Connection):
    """Abstract base class declaring the necessary attributes and methods for a USB connection."""

    @dataclass
    class USBConnectionSettings(Connection.ConnectionSettings):
        """Contains the settings of a connection."""

    settings: USBConnectionSettings

    @abstractmethod
    def _device_name(self) -> str:
        """Gets the device Instrument name."""

    @abstractmethod
    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
