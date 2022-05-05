from qililab.constants import (
    DEFAULT_PLATFORM_FILENAME,
    DEFAULT_SCHEMA_FILENAME,
    DEFAULT_SETTINGS_FOLDERNAME,
    YAML,
)
from qililab.platform.platform_manager import PlatformManager
from qililab.settings import SETTINGS_MANAGER
from qililab.typings import Category


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    PLATFORM_NAME = "platform_name"

    def _load_platform_settings(self, *args, **kwargs: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): The name of the platform.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
        if self.PLATFORM_NAME not in kwargs:
            raise ValueError(f"Please provide a '{self.PLATFORM_NAME}' keyword argument.")
        platform_name = kwargs[self.PLATFORM_NAME]
        return {
            YAML.SETTINGS: SETTINGS_MANAGER.load(
                foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform_name, filename=DEFAULT_PLATFORM_FILENAME
            ),
            Category.SCHEMA.value: SETTINGS_MANAGER.load(
                foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform_name, filename=DEFAULT_SCHEMA_FILENAME
            ),
        }
