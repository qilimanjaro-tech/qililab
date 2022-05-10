"""Mixer for up conversion. """
from qililab.instruments.mixer.mixer import Mixer
from qililab.typings import BusElementName
from qililab.utils import Factory


@Factory.register
class MixerUp(Mixer):
    """MixerUp class. Mixer used for up conversion."""

    name = BusElementName.MIXER_UP
