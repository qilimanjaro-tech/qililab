from dataclasses import dataclass
from typing import ClassVar

from qililab.config import logger
from qililab.settings import SM


@dataclass
class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        name (str): Name of the platform.
        platform_settings (Settings): Dataclass containing the settings of the platform.
    """

    name: str
    _id: ClassVar[str] = "platform"

    def __post_init__(self) -> None:
        """Load platform settings."""
        logger.info(f"Loading platform {self.name}")
        # TODO: Add "lab" (global?) variable instead of "qili"
        try:
            self.settings = SM.load(filename=self.name, category=self._id)
        except FileNotFoundError:
            raise NotImplementedError(f"Platform {self.name} is not defined.")

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.name
