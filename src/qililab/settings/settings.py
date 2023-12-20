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

"""Settings class."""
from dataclasses import dataclass
from types import NoneType
from typing import Any

from qililab.typings import Parameter
from qililab.utils.castings import cast_enum_fields


@dataclass(kw_only=True)
class Settings:
    """Settings class."""

    def __post_init__(self):
        """Cast all enum attributes to its corresponding Enum class."""
        cast_enum_fields(obj=self)

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Cast the new value to its corresponding type and set the new attribute.

        Args:
            parameter (Parameter): Name of the parameter.
            value (float | bool | str): Value of the parameter.
            channel_id (int | None, optional): Channel id. Defaults to None.

        Raises:
            ValueError: If the parameter is a list and channel_id is None.
        """
        param: str = parameter.value
        attribute = getattr(self, param)

        if isinstance(attribute, list):
            self._set_parameter_to_attribute_list(value=value, attributes=attribute, channel_id=channel_id)
            return
        self._set_parameter_to_attribute(parameter_name=param, value=value, attribute=attribute)

    def _set_parameter_to_attribute(self, value: float | str | bool, parameter_name: str, attribute: Any):
        """Set the parameter value to its corresponding attribute

        Args:
            value (float | str | bool): _description_
            parameter_name (str): _description_
            attribute (Any): _description_
        """
        attr_type = type(attribute)
        if attr_type == int:  # FIXME: Depending on how we define de value, python thinks it is an int
            attr_type = float
        if attr_type != NoneType:
            value = attr_type(value)
        setattr(self, parameter_name, value)

    def _set_parameter_to_attribute_list(
        self,
        value: float | str | bool,
        attributes: list[float | str | bool],
        channel_id: int | None,
    ):
        """Set the parameter value to its corresponding attribute list element

        Args:
            value (float | str | bool): _description_
            attribute (list[float  |  str  |  bool]): _description_
            channel_id (int | None): _description_
        """
        if channel_id is None:
            raise ValueError("No list index specified when updating a list of parameters.")
        if len(attributes) <= channel_id:
            raise ValueError(
                "Index out of bounds: Trying to update a list of parameters with length "
                + f"{len(attributes)} at position {channel_id}"
            )
        attributes[channel_id] = value

    def get_parameter(self, parameter: Parameter, channel_id: int | None = None):
        """Get parameter from settings.

        Args:
            parameter (Parameter): Name of the parameter.
            channel_id (int | None, optional): Channel id. Defaults to None.

        Raises:
            ValueError: If the parameter is a list and channel_id is None.

        Returns:
            int | float | bool | str: Value of the parameter.
        """
        param: str = parameter.value
        attribute = getattr(self, param)

        if isinstance(attribute, list):
            if channel_id is None:
                raise ValueError(f"channel_id must be specified to get parameter {param}.")
            return attribute[channel_id]
        return attribute
