from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class SetFrequency(Operation):
    bus: str
    frequency: int
