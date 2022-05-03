import sys
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path

import yaml

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_DUMP_FILENAME
from qililab.platform.components.schema import Schema
from qililab.platform.platform import Platform
from qililab.platform.utils import PlatformDict
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
        platform_dict = PlatformDict(**settings)
        schema = Schema(**asdict(platform_dict.schema))
        return Platform(settings=platform_dict.platform, schema=schema)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = Path(sys.argv[0]).parent / DEFAULT_PLATFORM_DUMP_FILENAME
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform.to_dict(), stream=file, sort_keys=False)

    @abstractmethod
    def _load_settings(self, **kwargs: str) -> dict:
        """Load platform and schema settings.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
