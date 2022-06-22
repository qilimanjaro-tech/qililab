"""Platform Manager"""
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from qililab.config import logger
from qililab.constants import RUNCARDS
from qililab.platform.platform import Platform
from qililab.platform.utils import RuncardSchema
from qililab.typings import yaml
from qililab.utils import SingletonABC


class PlatformManager(ABC, metaclass=SingletonABC):
    """Manager of platform objects."""

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform")
        platform_schema = RuncardSchema(**self._load_platform_settings(platform_name=platform_name))
        return Platform(runcard_schema=platform_schema)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = os.environ.get(RUNCARDS, None)
        if file_path is None:
            file_path = str(Path(sys.argv[0]).parent)
        file_path = f"{file_path}/{platform.name}.yml"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.dump(data=platform.to_dict(), stream=file, sort_keys=False)

    @abstractmethod
    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): The name of the platform.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
