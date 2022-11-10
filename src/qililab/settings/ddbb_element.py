"""Settings class."""
from dataclasses import dataclass, fields
from enum import Enum
from types import NoneType
from typing import Any

from qililab.typings import Category, Parameter


@dataclass(kw_only=True)
class DDBBElement:
    """Settings class.

    Args:
        id_ (str): ID of the settings.
        category (str): General name of the settings category. Options are "platform", "awg",
        "signal_generator", "qubit", "resonator", "mixer", "bus" and "schema".
        alias (str): Unique name identifying the element.
    """

    id_: int
    category: Category
    alias: str | None = None

    def __post_init__(self):
        """Cast all enum attributes to its corresponding Enum class."""
        for field in fields(self):
            if isinstance(field.type, type) and issubclass(field.type, Enum):
                setattr(self, field.name, field.type(getattr(self, field.name)))

    def set_parameter(self, parameter: Parameter, value: float | str | bool, parameter_index: int | None = None):
        """Cast the new value to its corresponding type and set the new attribute."""
        param: str = parameter.value
        attribute = getattr(self, param)

        if isinstance(attribute, list):
            self._set_parameter_to_attribute_list(value=value, attributes=attribute, parameter_index=parameter_index)
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
        parameter_index: int | None,
    ):
        """Set the parameter value to its corresponding attribute list element

        Args:
            value (float | str | bool): _description_
            attribute (list[float  |  str  |  bool]): _description_
            parameter_index (int | None): _description_
        """
        if parameter_index is None:
            raise ValueError("No list index specified when updating a list of parameters.")
        if len(attributes) <= parameter_index:
            raise ValueError(
                f"Index out of bounds: Trying to update a list of parameters with length {len(attributes)} at position {parameter_index}"
            )
        attributes[parameter_index] = value
