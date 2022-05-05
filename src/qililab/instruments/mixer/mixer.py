"""QubitReadout class."""
from qililab.settings import Settings
from qililab.typings import BusElement, Category
from qililab.utils import nested_dataclass


class Mixer(BusElement):
    """Mixer class. The mixer can be described by the following function:

    I + (1 + epsilon) * exp(j * pi/2 + delta) * Q, where I and Q are the two input signals.

    Due to the electronics, the mixer also adds a fixed offset to both I and Q channels.
    This offset should be evened out by the instrument.

    Args:
        settings (MixerSettings): Settings of the mixer.
    """

    category = Category.MIXER

    @nested_dataclass
    class MixerSettings(Settings):
        """Contains the settings of a mixer.

        Args:
            epsilon (float): Amplitude error added to the Q channel.
            delta (float): Dephasing added by the mixer.
            offset_i (float): Offset added to the I channel by the mixer.
            offset_q (float): Offset added to the Q channel by the mixer.
        """

        epsilon: float
        delta: float
        offset_i: float
        offset_q: float

    settings: MixerSettings

    def __init__(self, settings: dict):
        self.settings = self.MixerSettings(**settings)

    @property
    def id_(self):
        """Mixer 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def epsilon(self):
        """Mixer 'epsilon' property.

        Returns:
            float: settings.epsilon.
        """
        return self.settings.epsilon

    @property
    def delta(self):
        """Mixer 'delta' property.

        Returns:
            float: settings.delta.
        """
        return self.settings.delta

    @property
    def offset_i(self):
        """Mixer 'offset_i' property.

        Returns:
            float: settings.offset_i.
        """
        return self.settings.offset_i

    @property
    def offset_q(self):
        """Mixer 'offset_q' property.

        Returns:
            float: settings.offset_q.
        """
        return self.settings.offset_q
