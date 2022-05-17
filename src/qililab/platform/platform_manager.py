"""Platform Manager"""
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_DUMP_FILENAME
from qililab.platform.platform import Platform
from qililab.platform.utils import PlatformSchema
from qililab.utils import SingletonABC


class PlatformManager(ABC, metaclass=SingletonABC):
    """Manager of platform objects."""

    EXPERIMENT_SETTINGS = "exp_settings"

    def build(self, **kwargs: str | dict) -> Platform:
        """Build platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform")
        platform_schema = PlatformSchema(**self._load_platform_settings(**kwargs))
        return Platform(platform_schema=platform_schema)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = Path(sys.argv[0]).parent / DEFAULT_PLATFORM_DUMP_FILENAME
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform.to_dict(), stream=file, sort_keys=False)

    @abstractmethod
    def _load_platform_settings(self, **kwargs: str | dict) -> dict:
        """Load platform and schema settings.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
