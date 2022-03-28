from abc import ABC, abstractmethod

from qililab.config import logger


class AbstractPlatform(ABC):
    """Abstract platform for controlling quantum devices.

    Attributes:
        name (str): Name of the platform.
    """

    def __init__(self, name: str) -> None:
        """
        Args:
            name (str): Name of the platform
        """
        logger.info(f"Loading platform {name}")
        self.name = name

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.name
