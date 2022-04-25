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

    @property
    def id_(self):
        """Mixer 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Mixer 'name' property.

        Returns:
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Mixer 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

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

    @property
    def up_conversion(self):
        """Mixer 'up_conversion' property.

        Returns:
            float: settings.up_conversion.
        """
        return self.settings.up_conversion
