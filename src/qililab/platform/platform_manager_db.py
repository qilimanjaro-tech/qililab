"""PlatformManagerDB class."""
from .platform_manager import PlatformManager


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform settings.

        Args:
            platform_name (str): The name of the platform.

        Returns:
            dict: Dictionary with platform settings.
        """
        raise NotImplementedError
