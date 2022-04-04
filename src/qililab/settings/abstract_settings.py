from abc import ABC
from dataclasses import dataclass


@dataclass
class AbstractSettings(ABC):
    """Settings abstract class.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
        location (str): Path to location of settings file.
    """

    name: str
    category: str
    location: str
