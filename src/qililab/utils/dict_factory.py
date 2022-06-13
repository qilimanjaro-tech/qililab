"""Dict factory."""
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Dict, List

from qililab.typings import BusElement


def dict_factory(data):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values
    and all qubits with its corresponding settings dictionaries."""
    result: Dict[str, List[Dict[str, int | float | str]] | str | int | float] = {}
    for key, value in data:
        if isinstance(value, list):
            value = [
                asdict(element.settings, dict_factory=dict_factory) if isinstance(element, BusElement) else element
                for element in value
            ]
        elif isinstance(value, Enum):
            value = str(value.value)
        elif isinstance(value, BusElement):
            value = {"name": value.name.value} | asdict(value.settings, dict_factory=dict_factory)
        result = result | {key: value}
    return result
