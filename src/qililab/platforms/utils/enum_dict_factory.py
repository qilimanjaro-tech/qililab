from enum import Enum
from typing import Dict, List, Tuple


def enum_dict_factory(data: List[Tuple[str, int | float | str | Enum]]):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values."""
    result: Dict[str, int | float | str] = {}
    for key, value in data:
        if isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
