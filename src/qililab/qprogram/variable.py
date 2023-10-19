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


class Domain(Enum):
    Unitless = (0,)
    Time = (1,)
    Frequency = (2,)
    Phase = (3,)
    Voltage = 4


class ValueSource(Enum):
    Free = (0,)
    Dependent = 1


class Variable:
    """Variable class used to define variables inside a QProgram."""

    _uuid: UUID
    _value: int | float
    domain: Domain
    source: ValueSource = ValueSource.Free

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __init__(self):
        self._uuid = uuid4()

    def __str__(self):
        return str(self._uuid)

    def __repr__(self):
        return repr(self._uuid)

    def __hash__(self):
        return hash(self._uuid)

    def __format__(self, formatstr):
        return self._value.__format__(formatstr)

    def __pos__(self):
        return +self._value

    def __neg__(self):
        return -self._value

    def __abs__(self):
        return abs(self._value)

    def __round__(self, ndigits=None):
        return round(self._value, ndigits)

    def __floor__(self):
        return math.floor(self._value)

    def __ceil__(self):
        return math.ceil(self._value)

    def __trunc__(self):
        return math.trunc(self._value)

    def __int__(self):
        return int(self._value)

    def __float__(self):
        return float(self._value)

    def __complex__(self):
        return complex(self._value)

    def __add__(self, other):
        return self._value + other

    def __sub__(self, other):
        return self._value - other

    def __mul__(self, other):
        return self._value * other

    def __truediv__(self, other):
        return self._value / other

    def __floordiv__(self, other):
        return self._value // other

    def __mod__(self, other):
        return self._value % other

    def __pow__(self, other):
        return self._value**other

    def __radd__(self, other):
        return other + self._value

    def __rsub__(self, other):
        return other - self._value

    def __rmul__(self, other):
        return other * self._value

    def __rtruediv__(self, other):
        return other / self._value

    def __rfloordiv__(self, other):
        return other // self._value

    def __rmod__(self, other):
        return other % self._value

    def __rpow__(self, other):
        return other**self._value

    def __eq__(self, other):
        return self._value == other

    def __ne__(self, other):
        return self._value != other

    def __lt__(self, other):
        return self._value < other

    def __gt__(self, other):
        return self._value > other

    def __le__(self, other):
        return self._value <= other

    def __ge__(self, other):
        return self._value >= other


class IntVariable(Variable, int):  # type: ignore
    """Integer variable. This class is used to define a variable of type int, such that Python recognizes this class
    as an integer."""

    def __new__(cls, _: Domain = Domain.Unitless):
        # Create a new float instance
        instance = int.__new__(cls, 0)
        return instance

    def __init__(self, domain: Domain = Domain.Unitless):
        Variable.__init__(self)
        self.domain = domain


class FloatVariable(Variable, float):  # type: ignore
    """Float variable. This class is used to define a variable of type float, such that Python recognizes this class
    as a float."""

    def __new__(cls, _: Domain = Domain.Unitless):
        # Create a new int instance
        instance = float.__new__(cls, 0.0)
        return instance

    def __init__(self, domain: Domain = Domain.Unitless):
        Variable.__init__(self)
        self.domain = domain
