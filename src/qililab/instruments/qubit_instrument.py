"""QubitControl class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class QubitInstrument(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass
    class QubitInstrumentSettings(Instrument.InstrumentSettings):
        """Contains the settings of a QubitInstrument."""

    settings: QubitInstrumentSettings
