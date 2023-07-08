from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class SetAWGGain(Operation):
    bus: str
    gain_path0: float
    gain_path1: float
