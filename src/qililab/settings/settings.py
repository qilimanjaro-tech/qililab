from abc import ABC
from dataclasses import dataclass

from qililab.typings import CategorySettings


@dataclass
class Settings(ABC):
    """Settings class.

    Args:
        name (str): Name of the settings.
        category (str): Name of the settings category. Options are "platform", "instrument", "qubit" and "resonator".
    """

    name: str
    category: str | CategorySettings

    def __post_init__(self):
        """Cast category to its corresponding Enum class"""
        self.category = CategorySettings(self.category)
