from dataclasses import dataclass

from qililab.waveforms.waveform import Waveform


@dataclass
class IQPair:
    I: Waveform
    Q: Waveform
