from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class Wait(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    time: int
