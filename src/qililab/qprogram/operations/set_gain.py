from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class SetGain(Operation):
    bus: str
    gain: float
