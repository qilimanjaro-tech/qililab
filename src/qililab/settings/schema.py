from dataclasses import dataclass
from typing import Dict

from qililab.settings.settings import Settings


@dataclass
class SchemaSettings(Settings):
    """Schema settings.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator" and "schema".
        buses (Dict[str, Dict[str, Dict[str, str | int]]]): Dictionaries that describe the category
        and names of the elements located in each bus.
    """

    buses: Dict[str, Dict[str, Dict[str, str | int]]]
