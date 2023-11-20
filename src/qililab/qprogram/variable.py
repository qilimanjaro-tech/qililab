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


class Domain(Enum):
    """Domain class."""

    Scalar = (0,)
    Time = (1,)
    Frequency = (2,)
    Phase = (3,)
    Voltage = 4


class ValueSource(Enum):
    """ValueSource class"""

    Free = (0,)
    Dependent = 1


class Variable:
    """Variable class used to define variables inside a QProgram."""

    _uuid: UUID
    _value: int | float | None = None
    _source: ValueSource = ValueSource.Free
    domain: Domain

    @property
    def value(self):
        """Get the value of the variable

        Returns:
            int | float | None: The value of the variable
        """
        return self._value

    def __init__(self):
        self._uuid = uuid4()

    def __repr__(self):
        return repr(self._uuid)

    def __hash__(self):
        return hash(self._uuid)


class IntVariable(Variable, int):  # type: ignore
    """Integer variable. This class is used to define a variable of type int, such that Python recognizes this class
    as an integer."""

    def __new__(cls, _: Domain = Domain.Scalar):
        # Create a new float instance
        instance = int.__new__(cls, 0)
        return instance

    def __init__(self, domain: Domain = Domain.Scalar):
        Variable.__init__(self)
        self._value = None
        self.domain = domain


class FloatVariable(Variable, float):  # type: ignore
    """Float variable. This class is used to define a variable of type float, such that Python recognizes this class
    as a float."""

    def __new__(cls, _: Domain = Domain.Scalar):
        # Create a new int instance
        instance = float.__new__(cls, 0.0)
        return instance

    def __init__(self, domain: Domain = Domain.Scalar):
        Variable.__init__(self)
        self._value = None
        self.domain = domain
