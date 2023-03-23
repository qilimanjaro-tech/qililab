import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from inspect import signature
from typing import ClassVar, Dict, Tuple

from pytest import param

from qililab.circuit.operation_factory import OperationFactory

# from qililab.circuit.operation_factory import OperationFactory
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

    def __str__(self) -> str:
        result = self.name.value
        if self.has_parameters():
            parameters = ",".join([f"{name}={value}" for name, value in self.parameters.items()])
            result += f"({parameters})"
        return result

    @classmethod
    def parse(cls, string_representation: str):
        match = re.match(r"(\w+)(?:\(([\w]+=.+,?)\))?", string_representation)
        if match:
            operation_name, parameters_str = match.groups()
            operation_class = OperationFactory.get(operation_name)
            operation_signature = signature(operation_class)
            parameters = {}
            for parameter_str in parameters_str.split(","):
                name, value = parameter_str.split("=")
                parameter_signature = operation_signature.parameters.get(name)
                if parameter_signature is None:
                    raise ValueError(f"Operation {operation_name} has no parameter called {name}")
                value = parameter_signature.annotation(value)
                parameters[name] = value
            return operation_class(**parameters)
        else:
            raise ValueError(f"Invalid string representation: {string_representation}")
