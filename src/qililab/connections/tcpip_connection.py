"""TCPIPConnection class"""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.connections.connection import Connection


class TCPIPConnection(Connection):
    """Abstract base class declaring the necessary attributes and methods for a TCP-IP connection."""

    @dataclass
    class TCPIPConnectionSettings(Connection.ConnectionSettings):
        """Contains the settings of a connection."""

    settings: TCPIPConnectionSettings  # a subtype of settings must be specified by the subclass

    @abstractmethod
    def _device_name(self) -> str:
        """Gets the device Instrument name."""

    @abstractmethod
    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
