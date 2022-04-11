from dataclasses import dataclass

from qililab.schema import Schema
from qililab.settings.platform import PlatformSettings


@dataclass
class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        name (str): Name of the platform.
        settings (Settings): Dataclass containing the settings of the platform.
    """

    name: str
    settings: PlatformSettings
    schema: Schema
    # buses: Buses

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.name
