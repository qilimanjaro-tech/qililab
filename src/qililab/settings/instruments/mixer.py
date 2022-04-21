"""Mixer settings class"""
from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class MixerSettings(Settings):
    """Contains the settings of a mixer. The mixer can be described by the following function:

    I + (1 + epsilon) * exp(j * pi/2 + delta) * Q, where I and Q are the two input signals.

    Due to the electronics, the mixer also adds a fixed offset to both I and Q channels.
    This offset should be evened out by the instrument.

    Args:
        epsilon (float): Amplitude error added to the Q channel.
        delta (float): Dephasing added by the mixer.
        offset_i (float): Offset added to the I channel by the mixer.
        offset_q (float): Offset added to the Q channel by the mixer.
        up_conversion (bool): If True, mixer is used for up conversion. If False, mixer is used for down conversion.
    """

    epsilon: float
    delta: float
    offset_i: float
    offset_q: float
    up_conversion: bool
