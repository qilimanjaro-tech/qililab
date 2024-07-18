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

import copy
from dataclasses import dataclass

from qililab.qprogram.element import Element
from qililab.qprogram.variable import Variable


@dataclass
class Operation(Element):  # pylint: disable=missing-class-docstring
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
