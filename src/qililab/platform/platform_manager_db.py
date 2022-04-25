from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platform.platform_manager import PlatformManager
from qililab.settings import SETTINGS_MANAGER


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    def _load_platform_settings(self) -> dict:
        """Load platform settings.

        Returns:
            dict: Dictionary with platform settings.
        """
        return SETTINGS_MANAGER.load(platform_name=self.platform_name, filename=DEFAULT_PLATFORM_FILENAME)

    def _load_schema_settings(self) -> dict:
        """Load schema settings.

        Returns:
            dict: Dictionary with schema settings.
        """
        return SETTINGS_MANAGER.load(platform_name=self.platform_name, filename=DEFAULT_SCHEMA_FILENAME)
