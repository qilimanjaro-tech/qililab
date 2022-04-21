"""QubitControl class."""
from qililab.instruments.instrument import Instrument


class QubitControl(Instrument):
    """Abstract base class defining all instruments used to control the qubits

    Args:
        device (Device): Class used for connecting to the instrument.
        settings (Settings): Class containing the settings of the instrument.
    """
