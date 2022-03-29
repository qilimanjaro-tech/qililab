from abc import ABC, abstractmethod
from dataclasses import dataclass

from qililab.config import logger


@dataclass
class AbstractPlatform(ABC):
    """Abstract platform for controlling quantum devices.

    Args:
        name (str): Name of the platform.
    """

    name: str

    def __post_init__(self) -> None:
        """Log info message"""
        logger.info(f"Loading platform {self.name}")

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.name
