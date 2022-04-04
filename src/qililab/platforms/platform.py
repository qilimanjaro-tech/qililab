from dataclasses import dataclass

from qililab.schema import Schema
from qililab.settings.abstract_settings import AbstractSettings


@dataclass
class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        name (str): Name of the platform.
        settings (AbstracSettings): Dataclass containing the settings of the platform.
    """

    name: str
    settings: AbstractSettings
    schema: Schema
    # buses: Buses

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.name
