"""USBConnection class"""
from dataclasses import dataclass

from qililab.connections.connection import Connection


class USBConnection(Connection):
    """Abstract base class declaring the necessary attributes and methods for a USB connection."""

    @dataclass
    class USBConnectionSettings(Connection.ConnectionSettings):
        """Contains the settings of a connection."""

    settings: USBConnectionSettings
