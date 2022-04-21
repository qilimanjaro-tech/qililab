"""QubitReadout class."""
from qililab.instruments.instrument import Instrument


class QubitReadout(Instrument):
    """Abstract base class defining all instruments used to readout the qubits

    Args:
        device (Device): Class used for connecting to the instrument.
        settings (Settings): Class containing the settings of the instrument.
    """
