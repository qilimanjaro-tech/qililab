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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from qililab.qprogram.element import Element
from qililab.qprogram.variable import Variable

if TYPE_CHECKING:
    from qililab.qprogram.blocks.for_loop import ForLoop


class UnwrappingInformation:
    """Stores information about an Operation's unwrapping events."""

    def __init__(self):
        self.unwrapped_from: list[ForLoop] = []
        self.unwrapped_values: list[int | float] = []


@dataclass
class Operation(Element):  # pylint: disable=missing-class-docstring
    unwrapping: UnwrappingInformation = field(repr=False, compare=False, init=False, default=None)

    def get_variables(self) -> set[Variable]:
        """Get a set of the variables used in operation, if any.

        Returns:
            set[Variable]: The set of variables used in operation.
        """
        return {attribute for attribute in self.__dict__.values() if isinstance(attribute, Variable)}

    def replace_variables(self, variables: dict[Variable, int | float]) -> "Operation":
        """Replace variables in the operation with their values from the provided variable_map.

        Args:
            variable_map (dict[Variable, Union[int, float]]): Mapping of variables to their values.

        Returns:
            Operation: A new operation with variables replaced.
        """

        def replace(obj):
            """Recursively replace variables in the attributes of the given object."""
            for attribute, variable in obj.__dict__.items():
                if isinstance(variable, Variable) and variable in variables:
                    setattr(obj, attribute, variables[variable])
            return obj

        return replace(self)

    def replace_variables_from_unwrappings(self) -> "Operation":
        if not self.has_been_unwrapped:
            return self
        variables = {
            loop.variable: value
            for loop, value in zip(self.unwrapping.unwrapped_from, self.unwrapping.unwrapped_values)
        }
        return self.replace_variables(variables)

    @property
    def has_been_unwrapped(self) -> bool:
        """Checks if the operation has been unrwapped at least once.

        Returns:
            bool: True if the operation has been unwrapped, False otherwise.
        """
        return self.unwrapping is not None

    def add_unwrapping(self, unwrapped_from: "ForLoop", unwrapped_value: int | float) -> None:
        """Add an unwrapping event to the operation.

        Args:
            unwrapped_from (ForLoop): The loop that was unwrapped
            unwrapped_value (int | float): The variable's value for the specific operation
        """
        if self.unwrapping is None:
            self.unwrapping = UnwrappingInformation()
        self.unwrapping.unwrapped_from.append(unwrapped_from)
        self.unwrapping.unwrapped_values.append(unwrapped_value)
