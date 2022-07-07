"""USBConnection class"""
from dataclasses import dataclass

from qililab.connections.connection import Connection
from qililab.typings import ConnectionName
from qililab.utils import Factory


@Factory.register
@dataclass
class USBConnection(Connection):
    """Class declaring the necessary attributes and methods for an USB connection."""

    name = ConnectionName.USB
