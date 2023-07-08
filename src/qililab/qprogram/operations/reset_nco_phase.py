from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class ResetNCOPhase(Operation):
    bus: str
