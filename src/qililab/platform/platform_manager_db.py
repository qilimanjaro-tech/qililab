from qililab.constants import (
    DEFAULT_PLATFORM_FILENAME,
    DEFAULT_SCHEMA_FILENAME,
    DEFAULT_SETTINGS_FOLDERNAME,
)
from qililab.platform.platform_manager import PlatformManager
from qililab.settings import SETTINGS_MANAGER


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    def _load_all_settings(self, **kwargs: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): The name of the platform.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
        if "platform_name" not in kwargs:
            raise ValueError("Please provide a 'platform_name' argument.")
        platform_name = kwargs["platform_name"]
        return {
            "platform": SETTINGS_MANAGER.load(
                foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform_name, filename=DEFAULT_PLATFORM_FILENAME
            ),
            "schema": SETTINGS_MANAGER.load(
                foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform_name, filename=DEFAULT_SCHEMA_FILENAME
            ),
        }
