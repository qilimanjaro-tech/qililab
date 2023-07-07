from dataclasses import dataclass, field
from typing import Self  # type: ignore

from qililab.qprogram.operations.operation import Operation


@dataclass
class Block:
    elements: list[Self | Operation] = field(default_factory=list)

    def append(self, element: Self | Operation):
        self.elements.append(element)
