from dataclasses import asdict
from enum import Enum
from typing import Dict, List, Tuple

from qililab.platforms.components.qubit import Qubit
from qililab.platforms.utils.enum_dict_factory import enum_dict_factory
from qililab.settings import ResonatorSettings


class Resonator:
    """Resonator class"""

    settings: ResonatorSettings

    def __init__(self, settings: dict):
        self.settings = ResonatorSettings(**settings)

    def to_dict(self):
        """Return all Resonator information as a dictionary."""
        return asdict(self.settings, dict_factory=resonator_dict_factory)


def resonator_dict_factory(data: List[Tuple[str, int | float | str | Enum | List[Qubit]]]):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values
    and all qubits with its corresponding settings."""
    result: Dict[str, List[Dict[str, int | float | str]] | str | int | float] = {}
    for key, value in data:
        if isinstance(value, list):
            qubit_list: List[Dict[str, int | float | str]] = []
            for qubit in value:
                qubit_list.append(asdict(qubit.settings, dict_factory=enum_dict_factory))
            result = result | {key: qubit_list}
            continue
        if isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
