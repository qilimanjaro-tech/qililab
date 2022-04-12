from abc import ABC
from dataclasses import dataclass


@dataclass
class Settings(ABC):
    """Settings class.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
    """

    name: str
    category: str
