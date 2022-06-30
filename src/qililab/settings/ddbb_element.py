"""Settings class."""
from dataclasses import dataclass, fields
from enum import Enum
from types import NoneType

from qililab.typings import Category, Parameter


@dataclass(kw_only=True)
class DDBBElement:
    """Settings class.

    Args:
        id_ (str): ID of the settings.
        category (str): General name of the settings category. Options are "platform", "awg",
        "signal_generator", "qubit", "resonator", "mixer", "bus" and "schema".
    """

    id_: int
    category: Category
    alias: str | None = None

    def __post_init__(self):
        """Cast all enum attributes to its corresponding Enum class."""
        for field in fields(self):
            if isinstance(field.type, type) and issubclass(field.type, Enum):
                setattr(self, field.name, field.type(getattr(self, field.name)))

    def set_parameter(self, parameter: Parameter | str, value: float | str | bool):
        """Cast the new value to its corresponding type and set the new attribute."""
        if isinstance(parameter, Parameter):
            parameter = parameter.value
        attr_type = type(getattr(self, parameter))
        if attr_type == int:  # FIXME: Depending on how we define de value, python thinks it is an int
            attr_type = float
        if attr_type != NoneType:
            value = attr_type(value)
        setattr(self, parameter, value)
