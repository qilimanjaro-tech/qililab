"""QubitControl class."""
from qililab.instruments.instrument import Instrument
from qililab.settings import QubitControlSettings


class QubitControl(Instrument):
    """Abstract base class defining all instruments used to control the qubits."""

    settings: QubitControlSettings
