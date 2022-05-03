import sys
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_DUMP_FILENAME
from qililab.platform.components.buses import Buses
from qililab.platform.components.schema import Schema
from qililab.platform.platform import Platform
from qililab.typings import YAMLNames
from qililab.utils import SingletonABC


class PlatformManager(ABC, metaclass=SingletonABC):
    """Manager of platform objects."""

    def build(self, *args, **kwargs: str) -> Platform:
        """Build platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform")
        settings = self._load_settings(**kwargs)
        schema = self._build_schema(schema_settings=settings[YAMLNames.SCHEMA.value])
        return Platform(settings=settings[YAMLNames.PLATFORM.value], schema=schema)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = Path(sys.argv[0]).parent / DEFAULT_PLATFORM_DUMP_FILENAME
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform.to_dict(), stream=file, sort_keys=False)

    def _build_schema(self, schema_settings: dict):
        """Build schema from a given dictionary.

        Args:
            schema_settings (dict): Dictionary containing the schema settings.

        Returns:
            Schema: Schema object.
        """
        # TODO: To avoid having to check each key, we could create an object that accepts
        # a generic dictionary, and when calling a key does the check inside and throws a personalised error.
        if YAMLNames.BUSES.value not in schema_settings:
            raise ValueError(f"Schema settings must contain the {YAMLNames.BUSES.value} key.")
        buses_settings: list = schema_settings[YAMLNames.BUSES.value]

        buses = Buses(buses=buses_settings)

        return Schema(buses=buses)

    @abstractmethod
    def _load_settings(self, **kwargs: str) -> dict:
        """Load platform and schema settings.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
