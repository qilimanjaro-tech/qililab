from abc import ABC

from qililab.typings import Category
from qililab.utils import nested_dataclass


@nested_dataclass
class Settings(ABC):
    """Settings class.

    Args:
        id_ (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_instrument",
        "signal_generator", "qubit", "resonator", "mixer", "bus" and "schema".
    """

    id_: int
    name: str
    category: Category
