"""QubitReadout class."""
from qililab.instruments.instrument import Instrument
from qililab.settings import QubitReadoutSettings


class QubitReadout(Instrument):
    """Abstract base class defining all instruments used to readout the qubits."""

    settings: QubitReadoutSettings
