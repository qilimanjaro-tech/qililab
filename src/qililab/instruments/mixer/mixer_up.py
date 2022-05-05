"""Mixer for up conversion. """
from qililab.instruments.mixer.mixer import Mixer
from qililab.utils import BusElementFactory


@BusElementFactory.register
class MixerUp(Mixer):
    """MixerUp class. Mixer used for up conversion."""

    name = "mixer_up"
