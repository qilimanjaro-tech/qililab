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
    category: CategorySettings

    def __post_init__(self):
        """Cast category attribute to its corresponding Enum."""
        self.category = CategorySettings(self.category)
