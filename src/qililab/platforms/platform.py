from dataclasses import asdict

from qililab.platforms.components.buses import Buses
from qililab.platforms.components.schema import Schema
from qililab.platforms.utils.enum_dict_factory import enum_dict_factory
from qililab.settings import PlatformSettings
from qililab.typings import CategorySettings


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

    def to_dict(self):
        """Return all platform information as a dictionary."""
        if not hasattr(self, "schema") or not hasattr(self, "buses"):
            raise AttributeError("Platform is not loaded.")
        platform_dict = {CategorySettings.PLATFORM.value: asdict(self.settings, dict_factory=enum_dict_factory)}
        schema_dict = {CategorySettings.SCHEMA.value: self.schema.to_dict()}
        buses_dict = {CategorySettings.BUSES.value: self.buses.to_dict()}
        return platform_dict | schema_dict | buses_dict

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return str(self.to_dict())
