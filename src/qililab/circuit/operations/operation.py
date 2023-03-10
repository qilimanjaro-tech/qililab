from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import ClassVar, Dict, Tuple

from qililab.typings.enums import OperationMultiplicity
from qililab.typings.factory_element import FactoryElement
from qililab.utils import dict_factory

ParameterValue = int | float | bool
Parameters = Dict[str, ParameterValue]


@dataclass
class Operation(ABC):
    """Base class of all operations"""

    _name: str = field(init=False)
    _multiplicity: OperationMultiplicity = field(init=False)
    _parameters: Parameters = field(init=False, default_factory=dict)

    @property
    def name(self) -> str:
        return self._name

    @property
    def multiplicity(self) -> OperationMultiplicity:
        return self._multiplicity

    @property
    def parameters(self) -> Parameters:
        return self._parameters

    @property
    def parameter_names(self) -> Tuple[str, ...]:
        return tuple(self._parameters.keys())

    @property
    def parameter_values(self) -> Tuple[ParameterValue, ...]:
        return tuple(self._parameters.values())

    def has_parameters(self) -> bool:
        return len(self._parameters) > 0

    def set_parameter(self, parameter: str, value: ParameterValue):
        if parameter not in self._parameters:
            raise ValueError(f"Operation {self.name} has no parameter '{parameter}'")
        self._parameters[parameter] = value
        setattr(self, parameter, value)

    def get_parameter(self, parameter: str) -> ParameterValue:
        if parameter not in self._parameters:
            raise ValueError(f"Operation {self.name} has no parameter '{parameter}'")
        return self._parameters[parameter]
