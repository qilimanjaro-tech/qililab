# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Operation class

This file provides the abstract base class (ABC) Operation, which serves as the base class for all quantum operations in a quantum circuit.

It defines the ParameterValue and Parameters types for handling operation parameters.
The Operation class includes methods for setting and getting parameter values, as well as parsing a string representation of an operation to create an instance of the corresponding operation.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from inspect import Signature, signature

from qililab.circuit.operation_factory import OperationFactory
from qililab.typings import OperationName
from qililab.typings.enums import Qubits
from qililab.utils import classproperty

ParameterValue = int | float | bool
Parameters = dict[str, ParameterValue]


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
    def parameters_names(self) -> tuple[str, ...]:
        """Get the names of all parameters

        Returns:
            tuple[str, ...]: The names of all parameters as tuple
        """
        return tuple(self.parameters.keys())

    @property
    def parameters_values(self) -> tuple[ParameterValue, ...]:
        """Get the values of all parameters

        Returns:
            tuple[ParameterValue, ...]: The values of all parameters as tuple
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
        if match := re.match(r"(\w+)(?:\((\w+=.+,?)\))?", string_representation):
            operation_name, parameters_str = match.groups()
            operation_class = OperationFactory.get(operation_name)
            operation_signature = operation_class._get_signature()  # pylint: disable=protected-access
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
        raise ValueError(f"Invalid string representation: {string_representation}")
