from dataclasses import dataclass

from qililab.waveforms.waveform import Waveform


@dataclass
class IQPair:  # pylint: disable=missing-class-docstring
    I: Waveform
    Q: Waveform
