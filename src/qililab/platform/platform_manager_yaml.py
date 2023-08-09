"""PlatformManagerYAML class."""
import os

import yaml

from qililab.constants import RUNCARDS
from qililab.platform.platform_manager import PlatformManager


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform and transpilation settings.

        Args:
            platform_name (str): The name of the platform.

        Returns:
            dict: Dictionary with platform and transpilation settings.
        """
        runcards_path = os.environ.get(RUNCARDS, None)
        if runcards_path is None:
            raise ValueError("Environment variable RUNCARDS is not set.")

        with open(file=f"{runcards_path}/{platform_name}.yml", mode="r", encoding="utf8") as file:
            settings = yaml.safe_load(stream=file)

        return settings
