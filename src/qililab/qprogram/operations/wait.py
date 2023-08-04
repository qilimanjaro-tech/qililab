from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class Wait(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    time: int
