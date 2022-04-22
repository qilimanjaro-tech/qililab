from dataclasses import asdict
from enum import Enum
from typing import Dict, List


def dict_factory(data):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values
    and all qubits with its corresponding settings dictionaries."""
    result: Dict[str, List[Dict[str, int | float | str]] | str | int | float] = {}
    for key, value in data:
        if isinstance(value, list):
            result = result | {key: [asdict(qubit.settings, dict_factory=dict_factory) for qubit in value]}
            continue
        if isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
