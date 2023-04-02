# pylint: disable=no-member

import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from inspect import Signature, signature
from typing import ClassVar, Dict, Tuple

from pytest import param

from qililab.circuit.operation_factory import OperationFactory
from qililab.typings import OperationName
from qililab.typings.enums import OperationMultiplicity
from qililab.utils import classproperty

ParameterValue = int | float | bool
Parameters = Dict[str, ParameterValue]


@dataclass(kw_only=True)
class Operation(ABC):
    """Base class of all operations"""

    parameters: Parameters = field(init=False, default_factory=dict)
    _class_signature: Signature | None = None

    @classproperty
    @abstractmethod
    def name(self) -> OperationName:
        """Abstract property for the operation name."""

    @classproperty
    @abstractmethod
    def multiplicity(self) -> OperationMultiplicity:
        """Abstract property for the operation multiplicity."""

    @property
    def parameters_names(self) -> Tuple[str, ...]:
        """Get the names of all parameters

        Returns:
            Tuple[str, ...]: The names of all parameters as tuple
        """
        return tuple(self.parameters.keys())

    @property
    def parameters_values(self) -> Tuple[ParameterValue, ...]:
        """Get the values of all parameters

        Returns:
            Tuple[ParameterValue, ...]: The values of all parameters as tuple
        """
        return tuple(self.parameters.values())

    def has_parameters(self) -> bool:
        """Returns True if operation has settable parameters, False otherwise

        Returns:
            bool: True if operation has settable parameters, False otherwise
        """
        return len(self.parameters) > 0

    def set_parameter(self, name: str, value: ParameterValue):
        """Set parameter value

        Args:
            name (str): The name of the parameter
            value (ParameterValue): The new value of the parameter

        Raises:
            ValueError: If parameter does not exist
        """
        if name not in self.parameters:
            raise ValueError(f"Operation {self.name} has no parameter '{name}'")
        self.parameters[name] = value
        setattr(self, name, value)

    def get_parameter(self, name: str) -> ParameterValue:
        """Get parameter's value

        Args:
            name (str): The name of the parameter

        Raises:
            ValueError: If parapameter does not exist

        Returns:
            ParameterValue: The value of the parameter
        """
        if name not in self.parameters:
            raise ValueError(f"Operation {self.name} has no parameter '{name}'")
        return self.parameters[name]

    def __str__(self) -> str:
        """Return the string representation of the operation."""
        result = self.name.value
        if self.has_parameters():
            parameters = ",".join([f"{name}={value}" for name, value in self.parameters.items()])
            result += f"({parameters})"
        return result

    @classmethod
    def _get_signature(cls) -> Signature:
        """Get the signature of the class. Caches result for quicker retrievals.

        Returns:
            Signature: The signature of the class.
        """
        if cls._class_signature is None:
            cls._class_signature = signature(cls)
        return cls._class_signature

    @classmethod
    def parse(cls, string_representation: str):
        """
        Parse the string representation of an operation and return an instance of the operation.

        Args:
            string_representation (str): String representation of the operation.

        Returns:
            Operation: An instance of the parsed operation.
        """
        match = re.match(r"(\w+)(?:\((\w+=.+,?)\))?", string_representation)
        if match:
            operation_name, parameters_str = match.groups()
            operation_class = OperationFactory.get(operation_name)
            operation_signature = operation_class._get_signature()
            parameters = {}
            if parameters_str is not None:
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
