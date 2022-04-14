from qililab.buses import Bus, Buses
from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platforms.platform import Platform
from qililab.schema import Schema
from qililab.settings import SETTINGS_MANAGER
from qililab.utils import Singleton
from qililab.utils.name_hash_table import NameHashTable


class PlatformBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    platform_name: str
    platform: Platform

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform %s", platform_name)

        self.platform_name = platform_name
        SETTINGS_MANAGER.platform_name = platform_name

        self.build_platform()
        self.build_schema()
        self.build_buses()

        return self.platform

    def build_platform(self):
        """Build platform"""
        platform_set = SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)
        self.platform = Platform(name=self.platform_name, settings=platform_set)

    def build_schema(self):
        """Build schema"""
        schema_set = SETTINGS_MANAGER.load(filename=DEFAULT_SCHEMA_FILENAME)
        schema = Schema(settings=schema_set)
        self.platform.load_schema(schema=schema)

    def build_buses(self):
        """Build buses"""
        buses = Buses()
        schema = self.platform.schema
        for _, bus in schema.settings.buses.items():
            bus_settings = {}
            for _, item in bus.items():
                filename = f"""{item["name"]}_{item["id"]}"""
                settings = SETTINGS_MANAGER.load(filename=filename)
                element = getattr(NameHashTable, settings["name"])
                bus_settings[item["category"]] = element(settings)

            buses.append(Bus(**bus_settings))

        self.platform.load_buses(buses=buses)
