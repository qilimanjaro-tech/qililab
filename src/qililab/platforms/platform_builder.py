from dataclasses import dataclass

from qililab.config import logger
from qililab.platforms.platform import Platform
from qililab.settings import SM


@dataclass
class PlatformBuilder:
    """Builder of platform objects."""

    _instance = None

    def __new__(cls):
        """Instantiate the object only once.

        Returns:
            PlatformBuilder: Unique PlatformBuilder instance.
        """
        if cls._instance is None:
            cls._instance = super(PlatformBuilder, cls).__new__(cls)
        return cls._instance

    def build(self, name: str) -> Platform:
        """Build platform.

        Args:
            name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info(f"Building platform {name}")

        # TODO: Build platform (add corresponding classes...)

        try:
            settings = SM.load(filename=name, category="platform")
        except FileNotFoundError:
            raise NotImplementedError(f"Platform {name} is not defined.")

        return Platform(name=name, settings=settings)
