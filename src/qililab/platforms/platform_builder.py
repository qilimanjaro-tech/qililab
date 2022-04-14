from dataclasses import dataclass

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME
from qililab.platforms import Platform
from qililab.schema import Schema
from qililab.settings import SETTINGS_MANAGER
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
        schema_set = SETTINGS_MANAGER.load(filename="schema")
        schema = Schema(settings=schema_set)
        platform = Platform(name=name, settings=platform_set, schema=schema)

        return platform
