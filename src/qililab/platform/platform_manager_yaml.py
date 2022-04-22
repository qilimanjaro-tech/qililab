from typing import Dict

import yaml

from qililab.platform.platform import Platform
from qililab.platform.platform_manager import PlatformManager
from qililab.typings import CategorySettings


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    all_platform: Dict

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        if not hasattr(self, "all_platform"):
            raise AttributeError("Please use the 'build_from_yaml' method.")

        return super().build(platform_name=platform_name)

    def build_from_yaml(self, filepath: str) -> Platform:
        """Build platform from YAML file.

        Args:
            filepath (str): Path to the YAML file.

        Returns:
            Platform: Platform object describing the setup used.
        """
        self._load_yaml_data(filepath=filepath)
        return self.build(platform_name=self.all_platform["platform"]["name"])

    def _load_yaml_data(self, filepath: str):
        """Load YAML file and save it to all_platform attribute.

        Args:
            filepath (str): Path to the YAML file.
        """
        with open(file=filepath, mode="r", encoding="utf-8") as file:
            self.all_platform = yaml.safe_load(file)

    def _load_platform_settings(self):
        """Load platform settings."""
        return self.all_platform[CategorySettings.PLATFORM.value]

    def _load_schema_settings(self):
        """Load schema settings."""
        return self.all_platform[CategorySettings.SCHEMA.value]
