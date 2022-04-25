import yaml

from qililab.platform.platform_manager import PlatformManager
from qililab.typings import Category


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    FILEPATH = "filepath"

    def _load_settings(self, **kwargs: str) -> dict:
        """Load platform and schema settings.

        Args:
            filepath (str): Path of the YAML file.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
        if self.FILEPATH not in kwargs:
            raise ValueError(f"Please provide a '{self.FILEPATH}' argument.")
        filepath = kwargs[self.FILEPATH]
        with open(file=filepath, mode="r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        return {
            Category.PLATFORM.value: data[Category.PLATFORM.value],
            Category.SCHEMA.value: data[Category.SCHEMA.value],
        }
