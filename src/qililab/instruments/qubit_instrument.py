"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.instruments.pulse.pulse_sequence import PulseSequence


class QubitInstrument(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass
    class QubitInstrumentSettings(Instrument.InstrumentSettings):
        """Contains the settings of a QubitInstrument."""

    settings: QubitInstrumentSettings

    @abstractmethod
    def execute(self, pulse_sequence: PulseSequence):
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """
