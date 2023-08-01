from dataclasses import dataclass, field
from uuid import UUID, uuid4

from qililab.qprogram.element import Element
from qililab.qprogram.variable import Variable


@dataclass(frozen=True)
class Operation(Element):
    def get_variables(self) -> set[Variable]:
        return set([attribute for attribute in self.__dict__.values() if isinstance(attribute, Variable)])
