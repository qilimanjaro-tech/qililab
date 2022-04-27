"""QubitControl class."""
from dataclasses import dataclass

from qililab.instruments.qubit_instrument import QubitInstrument


class QubitControl(QubitInstrument):
    """Abstract base class defining all instruments used to control the qubits."""

    @dataclass
    class QubitControlSettings(QubitInstrument.QubitInstrumentSettings):
        """Contains the settings of a specific pulsar."""

    settings: QubitControlSettings
