import yaml

from qililab.platform.platform_manager import PlatformManager
from qililab.typings import Category


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    def _load_all_settings(self, **kwargs: str) -> dict:
        """Load platform and schema settings.

        Args:
            filepath (str): Path of the YAML file.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
        if "filepath" not in kwargs:
            raise ValueError("Please provide a 'filepath' argument.")
        filepath = kwargs["filepath"]
        with open(file=filepath, mode="r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        return {"platform": data[Category.PLATFORM.value], "schema": data[Category.SCHEMA.value]}
