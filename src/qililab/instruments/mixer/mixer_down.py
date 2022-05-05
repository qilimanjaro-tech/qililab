"""Mixer for down conversion."""
from qililab.instruments.mixer.mixer import Mixer
from qililab.typings import BusElementName
from qililab.utils import BusElementFactory


@BusElementFactory.register
class MixerDown(Mixer):
    """MixerUp class. Mixer used for up conversion."""

    name = BusElementName.MIXER_DOWN
