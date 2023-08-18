from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class SetGain(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    gain_path0: float
    gain_path1: float
