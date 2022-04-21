from abc import ABC
from dataclasses import dataclass

from qililab.typings import CategorySettings


@dataclass
class Settings(ABC):
    """Settings class.

    Args:
        id_ (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator", "mixer" and "schema".
    """

    id_: int
    name: str
    category: CategorySettings

    def __post_init__(self):
        """Cast category attribute to its corresponding Enum."""
        self.category = CategorySettings(self.category)
