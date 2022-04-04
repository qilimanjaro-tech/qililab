from dataclasses import dataclass

from qililab.config import logger
from qililab.platforms.platform import Platform
from qililab.schema import Schema
from qililab.settings import SM
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

        SM.platform = name

        # TODO: Build platform (add corresponding classes...)
        # Load settings
        platform_set = SM.load(filename="platform")
        schema_set = SM.load(filename="schema")
        schema = Schema(settings=schema_set)
        platform = Platform(name=name, settings=platform_set, schema=schema)

        return platform
