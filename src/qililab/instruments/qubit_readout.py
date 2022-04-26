"""QubitReadout class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class QubitReadout(Instrument):
    """Abstract base class defining all instruments used to readout the qubits."""

    @dataclass
    class QubitReadoutSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific pulsar."""

    settings: QubitReadoutSettings
