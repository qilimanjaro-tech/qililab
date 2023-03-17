from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import ClassVar, Dict, Tuple

from qililab.typings import OperationName
from qililab.typings.enums import OperationMultiplicity

ParameterValue = int | float | bool
Parameters = Dict[str, ParameterValue]


@dataclass
class Operation(ABC):
    """Base class of all operations"""

    name: OperationName = field(init=False)
    multiplicity: OperationMultiplicity = field(init=False)
    parameters: Parameters = field(init=False, default_factory=dict)

    @property
    def parameter_names(self) -> Tuple[str, ...]:
        return tuple(self.parameters.keys())

    @property
    def parameter_values(self) -> Tuple[ParameterValue, ...]:
        return tuple(self.parameters.values())

    def has_parameters(self) -> bool:
        return len(self.parameters) > 0

    def set_parameter(self, parameter: str, value: ParameterValue):
        if parameter not in self.parameters:
            raise ValueError(f"Operation {self.name} has no parameter '{parameter}'")
        self.parameters[parameter] = value
        setattr(self, parameter, value)

    def get_parameter(self, parameter: str) -> ParameterValue:
        if parameter not in self.parameters:
            raise ValueError(f"Operation {self.name} has no parameter '{parameter}'")
        return self.parameters[parameter]
