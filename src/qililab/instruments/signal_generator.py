"""SignalGenerator class."""
from qililab.instruments.instrument import Instrument


class SignalGenerator(Instrument):
    """Abstract base class defining all instruments used to generate signals.

    Args:
        device (Device): Class used for connecting to the instrument.
        settings (Settings): Class containing the settings of the instrument.
    """
