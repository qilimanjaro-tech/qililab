from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class SetPhase(Operation):
    bus: str
    phase: float
