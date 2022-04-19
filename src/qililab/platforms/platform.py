from dataclasses import asdict
from pathlib import Path

import yaml

from qililab.buses import Buses
from qililab.schema import Schema
from qililab.settings import PlatformSettings
from qililab.typings import dict_factory


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

    def dump(self):
        """Return all platform information as a dictionary."""
        if not hasattr(self, "schema") or not hasattr(self, "buses"):
            raise AttributeError("Platform is not loaded.")
        platform_dict = {"platform": asdict(self.settings, dict_factory=dict_factory)}
        schema_dict = {"schema": self.schema.asdict()}
        buses_dict = {"buses": self.buses.asdict()}
        file_path = Path(__file__).parent / "platform.yml"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform_dict | schema_dict | buses_dict, stream=file, sort_keys=False)

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.settings.name
