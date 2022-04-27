"""QubitReadout class."""
from dataclasses import dataclass

from qililab.instruments.qubit_instrument import QubitInstrument


class QubitReadout(QubitInstrument):
    """Abstract base class defining all instruments used to readout the qubits."""

    @dataclass
    class QubitReadoutSettings(QubitInstrument.QubitInstrumentSettings):
        """Contains the settings of a specific pulsar."""

    settings: QubitReadoutSettings
