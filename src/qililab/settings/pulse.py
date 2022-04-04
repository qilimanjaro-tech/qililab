from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class PulseSettings(Settings):
    """Contains the settings of a pulse.

    Args:
        amplitude (float): Amplitude of the pulse.
        duration (int): Duration of the pulse in nanoseconds.
        frequency (float): Frequency of the pulse in Hertz.
        offset_i (float): Offset applied to channel I.
        offset_q (float): Offset applied to channel Q.
    """

    amplitude: float
    duration: int  # ns
    frequency: float  # Hz
    offset_i: float
    offset_q: float
