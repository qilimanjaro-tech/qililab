from typing import Dict

from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platform.platform_manager import PlatformManager
from qililab.settings import SETTINGS_MANAGER, Settings
from qililab.typings import CategorySettings


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    def _load_platform_settings(self):
        """Load platform settings."""
        return SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)

    def _load_schema_settings(self):
        """Load schema settings."""
        return SETTINGS_MANAGER.load(filename=DEFAULT_SCHEMA_FILENAME)
