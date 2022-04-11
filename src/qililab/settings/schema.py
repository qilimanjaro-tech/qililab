from dataclasses import dataclass
from typing import Dict

from qililab.settings.settings import Settings


@dataclass
class SchemaSettings(Settings):
    """Schema settings.

    Args:
        buses (List[Dict[str, str]]): List of dictionaries that describe the category
        and names of the elements located in each bus.
    """

    buses: Dict[str, Dict[str, str]]
