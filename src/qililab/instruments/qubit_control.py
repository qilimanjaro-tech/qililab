"""QubitControl class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class QubitControl(Instrument):
    """Abstract base class defining all instruments used to control the qubits."""

    @dataclass
    class QubitControlSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific pulsar."""

    settings: QubitControlSettings
