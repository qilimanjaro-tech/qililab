"""BusElement class"""
from dataclasses import asdict
from enum import Enum
from typing import Dict, List

from qililab.constants import YAML
from qililab.typings.enums import Parameter
from qililab.typings.factory_element import FactoryElement
from qililab.typings.settings import SettingsType


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: SettingsType

    def set_parameter(self, parameter: Parameter | str, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        if isinstance(parameter, Parameter):
            parameter = parameter.value
        self.settings.set_parameter(name=parameter, value=value)

    def to_dict(self):
        """Return a dict representation of the BusElement class."""
        return {YAML.NAME: self.name.value} | asdict(self.settings, dict_factory=dict_factory)


def dict_factory(data):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values
    and all BusElement objects with its corresponding settings dictionaries."""
    result: Dict[str, List[Dict[str, int | float | str]] | str | int | float] = {}
    for key, value in data:
        if isinstance(value, list):
            value = [
                asdict(element.settings, dict_factory=dict_factory) if isinstance(element, BusElement) else element
                for element in value
            ]

        elif isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
