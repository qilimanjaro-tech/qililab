import sys
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from qililab.config import logger
from qililab.platform.components.buses import Buses
from qililab.platform.components.schema import Schema
from qililab.platform.platform import Platform
from qililab.settings import SETTINGS_MANAGER


class PlatformManager(ABC):
    """Manager of platform objects."""

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform %s", platform_name)

        SETTINGS_MANAGER.platform_name = platform_name

        schema = self._build_schema()
        buses = self._build_buses(schema=schema)
        return self._build_platform(schema=schema, buses=buses)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = Path(sys.argv[0]).parent / "all_platform.yml"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform.to_dict(), stream=file, sort_keys=False)

    def _build_platform(self, schema: Schema, buses: Buses) -> Platform:
        """Build platform."""
        platform_settings = self._load_platform_settings()
        return Platform(settings=platform_settings, schema=schema, buses=buses)

    def _build_schema(self) -> Schema:
        """Build platform schema."""
        schema_settings = self._load_schema_settings()
        return Schema(settings=schema_settings)

    def _build_buses(self, schema: Schema) -> Buses:
        """Build platform buses."""
        return Buses(schema.buses)

    @abstractmethod
    def _load_platform_settings(self):
        """Load platform settings."""

    @abstractmethod
    def _load_schema_settings(self):
        """Load schema settings."""
