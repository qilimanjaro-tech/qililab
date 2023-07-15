from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQPair


@dataclass
class Acquire(Operation):
    bus: str
    weights: IQPair | None
