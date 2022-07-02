"""TCPIPConnection class"""
from dataclasses import dataclass

from qililab.connections.connection import Connection


class TCPIPConnection(Connection):
    """Abstract base class declaring the necessary attributes and methods for a TCP-IP connection."""

    @dataclass
    class TCPIPConnectionSettings(Connection.ConnectionSettings):
        """Contains the settings of a connection."""

    settings: TCPIPConnectionSettings  # a subtype of settings must be specified by the subclass
