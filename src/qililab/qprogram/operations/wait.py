from dataclasses import dataclass, field

from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class Wait(Operation):
    bus: str
    time: int
