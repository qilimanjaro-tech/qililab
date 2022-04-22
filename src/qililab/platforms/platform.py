import sys
from dataclasses import asdict
from pathlib import Path

import yaml

from qililab.buses import Buses
from qililab.schema import Schema
from qililab.settings import PlatformSettings
from qililab.typings import CategorySettings, enum_dict_factory


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        settings (Settings): Settings of the platform.
        schema (Schema): Schema object.
        buses (Buses): Container of Bus objects.
    """

    def __init__(self, settings: dict, schema: Schema, buses: Buses):
        self.settings = PlatformSettings(**settings)
        self.schema = schema
        self.buses = buses

    @property
    def name(self):
        """Return name from settings"""
        return self.settings.name

    def dump(self):
        """Return all platform information as a dictionary."""
        if not hasattr(self, "schema") or not hasattr(self, "buses"):
            raise AttributeError("Platform is not loaded.")
        platform_dict = {CategorySettings.PLATFORM.value: asdict(self.settings, dict_factory=enum_dict_factory)}
        schema_dict = {CategorySettings.SCHEMA.value: self.schema.asdict()}
        buses_dict = {CategorySettings.BUSES.value: self.buses.asdict()}
        file_path = Path(sys.argv[0]).parent / "platform.yml"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform_dict | schema_dict | buses_dict, stream=file, sort_keys=False)

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.settings.name
