from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class SetNCOPhase(Operation):
    bus: str
    phase: float
