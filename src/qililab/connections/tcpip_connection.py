"""TCPIPConnection class"""

from qililab.connections.connection import Connection
from qililab.typings import ConnectionName
from qililab.utils import Factory


@Factory.register
class TCPIPConnection(Connection):
    """Class declaring the necessary attributes and methods for a TCP-IP connection."""

    name = ConnectionName.TCP_IP
