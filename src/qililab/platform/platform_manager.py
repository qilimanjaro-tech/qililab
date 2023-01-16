"""Platform Manager"""
import os
from abc import ABC, abstractmethod

from qililab.config import logger
from qililab.constants import RUNCARDS
from qililab.platform.platform import Platform
from qililab.typings import yaml
from qililab.utils import SingletonABC


class PlatformManager(ABC, metaclass=SingletonABC):
    """Manager of platform objects."""

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform to load.

        Returns:
            Platform: Platform object describing the setup used.
        """

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        runcards_path = os.environ.get(RUNCARDS, None)
        if runcards_path is None:
            raise ValueError("Environment variable RUNCARDS is not set.")
        file_path = f"{runcards_path}/{platform.name}.yml"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.dump(data=platform.to_dict(), stream=file, sort_keys=False)

    @abstractmethod
    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): Name of the runcard  to load settings and schema from

        Returns:
            dict: Dictionary with platform and schema settings.
        """
