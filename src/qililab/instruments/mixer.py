"""QubitReadout class."""
from qililab.settings import MixerSettings


class Mixer:
    """Mixer class. The mixer can be described by the following function:

    I + (1 + epsilon) * exp(j * pi/2 + delta) * Q, where I and Q are the two input signals.

    Due to the electronics, the mixer also adds a fixed offset to both I and Q channels.
    This offset should be evened out by the instrument.

    Args:
        settings (MixerSettings): Settings of the mixer.
    """

    settings: MixerSettings

    def __init__(self, settings: dict):
        self.settings = MixerSettings(**settings)
