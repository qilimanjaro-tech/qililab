from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQPair, Waveform


@dataclass
class Play(Operation):
    bus: str
    waveform: Waveform | IQPair
