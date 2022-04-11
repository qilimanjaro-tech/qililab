from dataclasses import dataclass

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME
from qililab.platforms.platform import Platform
from qililab.schema import Schema
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.platform_settings import PlatformSettings
from qililab.settings.schema_settings import SchemaSettings
from qililab.utils import Singleton


@dataclass
class PlatformBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, name: str) -> Platform:
        """Build platform.

        Args:
            name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform %s", name)

        SETTINGS_MANAGER.platform_name = name

        # TODO: Build platform (add corresponding classes...)
        # Load settings
        platform_set = SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)
        if not isinstance(platform_set, PlatformSettings):
            raise ValueError(f"Using wrong class {type(platform_set)} for platform settings.")
        schema_set = SETTINGS_MANAGER.load(filename="schema")
        if not isinstance(schema_set, SchemaSettings):
            raise ValueError(f"Using wrong class {type(platform_set)} for schema settings.")
        schema = Schema(settings=schema_set)
        platform = Platform(name=name, settings=platform_set, schema=schema)

        return platform
