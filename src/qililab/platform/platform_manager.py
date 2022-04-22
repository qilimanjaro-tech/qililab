import copy
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

import yaml

from qililab.config import logger
from qililab.platform.components.bus import Bus
from qililab.platform.components.buses import Buses
from qililab.platform.components.schema import Schema
from qililab.platform.platform import Platform
from qililab.platform.utils.bus_element_hash_table import BusElementHashTable
from qililab.settings import SETTINGS_MANAGER, Settings
from qililab.typings import CategorySettings


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
        file_path = Path(sys.argv[0]).parent / "platform.yml"
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
        buses = Buses()
        for bus in schema.settings.buses:
            bus_kwargs = {}
            for item in bus:
                settings = self._load_bus_item_settings(item=item)
                element = self._load_bus_element(settings=settings)
                bus_kwargs[item.category.value] = element

            buses.append(Bus(**bus_kwargs))

        return buses

    def _load_bus_element(self, settings: dict):
        """Load class instance of the corresponding category.

        Args:
            settings (dict): Settings of the category object.

        Returns:
            (Platform | QbloxPulsarQRM | QbloxPulsarQCM | SGS100A | Resonator | Qubit): Class instance of the element.
        """
        element_type = BusElementHashTable.get(settings["name"])

        return element_type(settings)

    @abstractmethod
    def _load_platform_settings(self):
        """Load platform settings."""

    @abstractmethod
    def _load_schema_settings(self):
        """Load schema settings."""

    @abstractmethod
    def _load_bus_item_settings(self, item: Settings):
        """Load settings of the corresponding bus item.

        Args:
            item (Settings): Settings class containing the settings of the item.
        """
