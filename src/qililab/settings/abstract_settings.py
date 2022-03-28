from abc import ABC
from dataclasses import dataclass


@dataclass
class AbstractSettings(ABC):
    """Settings abstract class.

    Args:
        name (str): Name of the settings.
        location (str): Path to location of settings file.
    """

    name: str
    location: str
