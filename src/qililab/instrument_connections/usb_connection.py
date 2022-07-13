"""USBConnection class"""

from qililab.instrument_connections.connection import Connection
from qililab.typings import ConnectionName
from qililab.utils import Factory


@Factory.register
class USBConnection(Connection):
    """Class declaring the necessary attributes and methods for an USB connection."""

    name = ConnectionName.USB
