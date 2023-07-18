from __future__ import annotations

from dataclasses import dataclass, field

from qililab.qprogram.operations.operation import Operation


@dataclass(kw_only=True)
class Block:
    elements: list[Block | Operation] = field(default_factory=list, init=False)

    def append(self, element: Block | Operation):
        self.elements.append(element)
