import sys
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from qililab.constants import DEFAULT_PLATFORM_DUMP_FILENAME
from qililab.platform.components.buses import Buses
from qililab.platform.components.schema import Schema
from qililab.platform.platform import Platform
from qililab.typings import YAMLNames
from qililab.utils import SingletonABC


class PlatformManager(ABC, metaclass=SingletonABC):
    """Manager of platform objects."""

    def build(self, **kwargs: str) -> Platform:
        """Build platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        settings = self._load_all_settings(**kwargs)
        schema = Schema(settings=settings[YAMLNames.SCHEMA.value])
        buses = Buses(buses=schema.buses)
        return Platform(settings=settings[YAMLNames.PLATFORM.value], schema=schema, buses=buses)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = Path(sys.argv[0]).parent / DEFAULT_PLATFORM_DUMP_FILENAME
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform.to_dict(), stream=file, sort_keys=False)

    @abstractmethod
    def _load_all_settings(self, **kwargs: str) -> dict:
        """Load platform and schema settings.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
