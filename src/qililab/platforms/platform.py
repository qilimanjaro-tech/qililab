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
