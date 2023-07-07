from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class SetNCOFrequency(Operation):
    bus: str
    frequency: int
