"""PlatformManagerYAML class."""
import os

import yaml

from qililab.config import logger
from qililab.constants import RUNCARDS
from qililab.platform.platform import Platform
from qililab.platform.platform_manager import PlatformManager
from qililab.settings import RuncardSchema


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the runcard file to load as a platform

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform")
        platform_settings = self._load_platform_settings(platform_name=platform_name)
        platform_schema = RuncardSchema(**platform_settings)
        return Platform(runcard_schema=platform_schema)

    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): Name of the runcard file to read settings and schema from

        Returns:
            dict: Dictionary with platform and schema settings.
        """
        runcards_path = os.environ.get(RUNCARDS, None)
        if runcards_path is None:
            raise ValueError("Environment variable RUNCARDS is not set.")

        with open(file=f"{runcards_path}/{platform_name}.yml", mode="r", encoding="utf8") as file:
            settings = yaml.safe_load(stream=file)

        return settings
