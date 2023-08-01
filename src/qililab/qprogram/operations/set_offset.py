from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class SetOffset(Operation):
    bus: str
    offset_path0: float
    offset_path1: float
