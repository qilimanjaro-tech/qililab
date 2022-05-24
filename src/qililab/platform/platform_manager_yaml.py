"""PlatformManagerYAML class."""
import yaml

from qililab.constants import YAML
from qililab.platform.platform_manager import PlatformManager
from qililab.typings import Category


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    FILEPATH = "filepath"

    def _load_platform_settings(self, **kwargs: str | dict) -> dict:
        """Load platform and schema settings.

        Args:
            filepath (str): Path of the YAML file.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
        if self.FILEPATH not in kwargs:
            raise ValueError(f"Please provide a '{self.FILEPATH}' keyword argument.")

        filepath = kwargs[self.FILEPATH]

        if not isinstance(filepath, str):
            raise ValueError(f"Please provide a string in the '{self.FILEPATH}' keyword argument.")

        with open(file=filepath, mode="r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        return {
            YAML.SETTINGS: data[YAML.SETTINGS],
            Category.SCHEMA.value: data[Category.SCHEMA.value],
        }
