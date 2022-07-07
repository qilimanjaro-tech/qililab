"""dict_factory used for dataclass' asdict method."""
from enum import Enum
from typing import Dict, List


def dict_factory(data):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values
    and all BusElement objects with its corresponding settings dictionaries."""
    result: Dict[str, List[Dict[str, int | float | str]] | str | int | float] = {}
    for key, value in data:
        if isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
