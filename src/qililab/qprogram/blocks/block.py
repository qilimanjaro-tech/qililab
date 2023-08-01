from __future__ import annotations

from dataclasses import dataclass, field

from qililab.qprogram.element import Element
from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class Block(Element):
    elements: list[Block | Operation] = field(default_factory=list, init=False)

    def append(self, element: Block | Operation):
        self.elements.append(element)
