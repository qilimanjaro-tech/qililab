"""PlatformManagerDB class."""
from qililab.platform.platform_manager import PlatformManager


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): The name of the platform.

        Returns:
            dict: Dictionary with platform and schema settings.
        """
        raise NotImplementedError