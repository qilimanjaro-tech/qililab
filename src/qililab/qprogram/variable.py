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

"""This file contains all the variables used inside a QProgram."""

from enum import Enum
from uuid import UUID, uuid4

from qililab.yaml import yaml


@yaml.register_class
class Domain(Enum):
    """Domain class."""

    Scalar = 0
    Time = 1
    Frequency = 2
    Phase = 3
    Voltage = 4
    Flux = 5

    @classmethod
    def to_yaml(cls, representer, node):
        """Method to be called automatically during YAML serialization."""
        return representer.represent_scalar("!Domain", f"{node.name}-{node.value}")

    @classmethod
    def from_yaml(cls, _, node):
        """Method to be called automatically during YAML deserialization."""
        _, value = node.value.split("-")
        value = int(value)
        return cls(value)


@yaml.register_class
class Variable:
    """Variable class used to define variables inside a QProgram."""

    def __init__(self, label: str, domain: Domain = Domain.Scalar) -> None:
        self._uuid: UUID = uuid4()
        self._label: str = label
        self._domain: Domain = domain

    def __repr__(self):
        return f"Variable(uuid={self.uuid!r}, label={self.label}, domain={self.domain})"

    def __hash__(self):
        return hash(self._uuid)

    def __eq__(self, other):
        return other is not None and isinstance(other, Variable) and self._uuid == other._uuid

    @property
    def uuid(self):
        """Get the uuid of the variable

        Returns:
            UUID: The uuid of the variable
        """
        return self._uuid

    @property
    def label(self):
        """Get the label of the variable

        Returns:
            str: The label of the variable
        """
        return self._label

    @property
    def domain(self):
        """Get the domain of the variable

        Returns:
            Domain: The domain of the variable
        """
        return self._domain


@yaml.register_class
class IntVariable(Variable, int):  # type: ignore
    """Integer variable. This class is used to define a variable of type int, such that Python recognizes this class
    as an integer."""

    def __new__(cls, _: str = "", __: Domain = Domain.Scalar):
        # Create a new float instance
        instance = int.__new__(cls, 0)
        return instance

    def __init__(self, label: str = "", domain: Domain = Domain.Scalar):
        Variable.__init__(self, label, domain)


@yaml.register_class
class FloatVariable(Variable, float):  # type: ignore
    """Float variable. This class is used to define a variable of type float, such that Python recognizes this class
    as a float."""

    def __new__(cls, _: str = "", __: Domain = Domain.Scalar):
        # Create a new int instance
        instance = float.__new__(cls, 0.0)
        return instance

    def __init__(self, label: str = "", domain: Domain = Domain.Scalar):
        Variable.__init__(self, label, domain)
