from dataclasses import dataclass

from qililab.qprogram.element import Element
from qililab.qprogram.variable import Variable


@dataclass(frozen=True)
class Operation(Element):  # pylint: disable=missing-class-docstring
    def get_variables(self) -> set[Variable]:
        """Get a set of the variables used in operation, if any.

        Returns:
            set[Variable]: The set of variables used in operation.
        """
        return {attribute for attribute in self.__dict__.values() if isinstance(attribute, Variable)}
