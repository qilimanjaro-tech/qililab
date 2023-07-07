from dataclasses import dataclass, field
from typing import Self  # type: ignore

from qililab.qprogram.operations.operation import Operation


@dataclass(kw_only=True)
class Block:
    elements: list[Self | Operation] = field(default_factory=list, init=False)

    def append(self, element: Self | Operation):
        self.elements.append(element)
