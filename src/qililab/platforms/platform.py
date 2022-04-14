from qililab.buses import Buses
from qililab.schema import Schema
from qililab.settings import PlatformSettings


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        name (str): Name of the platform.
        settings (Settings): Dataclass containing the settings of the platform.
    """

    schema: Schema
    buses: Buses

    def __init__(self, settings: dict):
        self.settings = PlatformSettings(**settings)

    def load_schema(self, schema: Schema):
        """Load schema

        Args:
            schema (Schema): Schema of the platform.
        """
        self.schema = schema

    def load_buses(self, buses: Buses):
        """Load buses

        Args:
            buses (Buses): Container of buses of the platform.
        """
        self.buses = buses

    @property
    def name(self):
        """Return name from settings"""
        return self.settings.name

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.settings.name
