"""QubitReadout class."""
from qililab.settings import MixerSettings


class Mixer:
    """Abstract base class defining all instruments used to readout the qubits

    Args:
        device (Device): Class used for connecting to the instrument.
        settings (Settings): Class containing the settings of the instrument.
    """

    settings: MixerSettings

    def __init__(self, settings: dict):
        self.settings = MixerSettings(**settings)
