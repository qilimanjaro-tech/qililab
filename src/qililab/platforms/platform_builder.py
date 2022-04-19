from dataclasses import dataclass

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME
from qililab.platforms import Platform
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

        try:
            settings = SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)
        except FileNotFoundError as file_not_found:
            raise NotImplementedError(f"Platform {name} is not defined.") from file_not_found

        return Platform(name=name, settings=settings)
