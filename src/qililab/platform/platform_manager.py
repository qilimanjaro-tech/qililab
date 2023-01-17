"""Platform Manager"""

from abc import ABC, abstractmethod

from qililab.platform.platform import Platform
from qililab.utils import SingletonABC


class PlatformManager(ABC, metaclass=SingletonABC):
    """Manager of platform objects."""

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform to load.

        Returns:
            Platform: Platform object describing the setup used.
        """

    def dump(self, platform: Platform):
        """Save all platform information.

        Args:
            platform (Platform): Platform to save.
        """

    @abstractmethod
    def _load_platform_settings(self, platform_name: str) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): Name of the runcard  to load settings and schema from

        Returns:
            dict: Dictionary with platform and schema settings.
        """
