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
import math
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
class ValueSource(Enum):
    """ValueSource class"""

    Free = 0
    Dependent = 1

    @classmethod
    def to_yaml(cls, representer, node):
        """Method to be called automatically during YAML serialization."""
        return representer.represent_scalar("!ValueSource", f"{node.name}-{node.value}")

    @classmethod
    def from_yaml(cls, _, node):
        """Method to be called automatically during YAML deserialization."""
        _, value = node.value.split("-")
        value = int(value)
        return cls(value)


@yaml.register_class
class Variable:
    """Variable class used to define variables inside a QProgram."""

    def __init__(self, domain: Domain = Domain.Scalar) -> None:
        self._uuid: UUID = uuid4()
        self._source: ValueSource = ValueSource.Free
        self._value: int | float | None = None
        self._domain: Domain = domain

    @property
    def value(self):
        """Get the value of the variable

        Returns:
            int | float | None: The value of the variable
        """
        return self._value

    @value.setter
    def value(self, new_value):
        """Set the value of the variable

        Args:
            new_value (int | float | None): The new value to set
        """
        if not isinstance(new_value, (int, float)):
            raise ValueError("Value must be an int or float.")
        if isinstance(self, IntVariable):
            self._value = int(new_value)
        else:
            self._value = float(new_value)

    @property
    def domain(self):
        """Get the domain of the variable

        Returns:
            Domain: The domain of the variable
        """
        return self._domain

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self._uuid)

    def __format__(self, formatstr):
        return self.value.__format__(formatstr)

    def __pos__(self):
        return +self.value  # pylint: disable=invalid-unary-operand-type

    def __neg__(self):
        return -self.value  # pylint: disable=invalid-unary-operand-type

    def __abs__(self):
        return abs(self.value)

    def __round__(self, ndigits=None):
        return round(self.value, ndigits)

    def __floor__(self):
        return math.floor(self.value)

    def __ceil__(self):
        return math.ceil(self.value)

    def __trunc__(self):
        return math.trunc(self.value)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __complex__(self):
        return complex(self.value)

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __floordiv__(self, other):
        return self.value // other

    def __mod__(self, other):
        return self.value % other

    def __pow__(self, other):
        return self.value**other

    def __radd__(self, other):
        return other + self.value

    def __rsub__(self, other):
        return other - self.value

    def __rmul__(self, other):
        return other * self.value

    def __rtruediv__(self, other):
        return other / self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rmod__(self, other):
        return other % self.value

    def __rpow__(self, other):
        return other**self.value

    def __eq__(self, other):
        return other is not None and isinstance(other, Variable) and self._value == other._value

    def __lt__(self, other):
        return self.value < other

    def __le__(self, other):
        return self.value <= other

    def __gt__(self, other):
        return self.value > other

    def __ge__(self, other):
        return self.value >= other


@yaml.register_class
class IntVariable(Variable, int):  # type: ignore
    """Integer variable. This class is used to define a variable of type int, such that Python recognizes this class
    as an integer."""

    def __new__(cls, _: Domain = Domain.Scalar):
        # Create a new float instance
        instance = int.__new__(cls, 0)
        return instance

    def __init__(self, domain: Domain = Domain.Scalar):
        Variable.__init__(self, domain)


@yaml.register_class
class FloatVariable(Variable, float):  # type: ignore
    """Float variable. This class is used to define a variable of type float, such that Python recognizes this class
    as a float."""

    def __new__(cls, _: Domain = Domain.Scalar):
        # Create a new int instance
        instance = float.__new__(cls, 0.0)
        return instance

    def __init__(self, domain: Domain = Domain.Scalar):
        Variable.__init__(self, domain)
