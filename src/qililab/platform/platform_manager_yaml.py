"""PlatformManagerYAML class."""
from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.platform.platform_manager import PlatformManager
from qililab.settings import SETTINGS_MANAGER


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): The name of the platform.

        Returns:
            dict: Dictionary with platform and schema settings.
        """

        return SETTINGS_MANAGER.load(foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform_name)
