from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class SetFrequency(Operation):
    bus: str
    frequency: float
