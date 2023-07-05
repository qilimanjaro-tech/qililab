from dataclasses import dataclass, field

from qililab.qprogram.operations.operation import Operation


@dataclass
class Block:
    elements: list["Block" | Operation] = field(default_factory=list)

    def append(self, element: "Block" | Operation):
        self.elements.append(element)
