"""Operation class

This file provides the abstract base class (ABC) Operation, which serves as the base class for all quantum operations in a quantum circuit.

It defines the ParameterValue and Parameters types for handling operation parameters.
The Operation class includes methods for setting and getting parameter values, as well as parsing a string representation of an operation to create an instance of the corresponding operation.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from inspect import Signature, signature
from multiprocessing.pool import RUN
from typing import Dict, Tuple

from qililab.circuit.operation_factory import OperationFactory
from qililab.constants import RUNCARD
from qililab.typings import OperationName
from qililab.typings.enums import Qubits
from qililab.utils import classproperty

ParameterValue = int | float | bool
Parameters = Dict[str, ParameterValue]


@dataclass(kw_only=True)
class Operation(ABC):
    """Base class of all operations"""

    _class_signature: Signature | None = None

    @classproperty
    @abstractmethod
    def name(self) -> OperationName:
        """Abstract property for the operation name."""

    @classproperty
    @abstractmethod
    def num_qubits(self) -> Qubits:
        """Abstract property for the operation multiplicity."""

    @property
    def parameters(self) -> Parameters:
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {}

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
        """Set parameter's value

        Args:
            name (str): The name of the parameter
            value (ParameterValue): The new value of the parameter

        Raises:
            ValueError: If parameter does not exist
        """
        if not (hasattr(self, name) and name in self.parameters):
            raise ValueError(f"Operation {self.name} has no parameter '{name}'")
        setattr(self, name, value)

    def get_parameter(self, name: str) -> ParameterValue:
        """Get parameter's value

        Args:
            name (str): The name of the parameter

        Raises:
            ValueError: If parameter does not exist

        Returns:
            ParameterValue: The value of the parameter
        """
        if not (hasattr(self, name) and name in self.parameters):
            raise ValueError(f"Operation {self.name} has no parameter '{name}'")
        return getattr(self, name)

    def __str__(self) -> str:
        """Get the string representation of the operation

        Returns:
            str: The string representation of the operation
        """
        result = self.name.value  # pylint: disable=no-member
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

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load Pulse object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Pulse object.

        Returns:
            Pulse: Loaded class.
        """
        operation_class = OperationFactory.get(dictionary.pop(RUNCARD.NAME))
        return operation_class(**dictionary)

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {RUNCARD.NAME: self.name} | self.parameters
