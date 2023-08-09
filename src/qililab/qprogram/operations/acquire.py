from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQPair


@dataclass
class Acquire(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    weights: IQPair | None
