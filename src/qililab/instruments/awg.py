"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path

from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseSequence
from qililab.result import QbloxResult


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass
    class AWGSettings(Instrument.InstrumentSettings):
        """Contains the settings of a AWG.

        Args:
            frequency (float): Intermediate frequency (IF).
            offset_i (float): I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (float): Q offset (unitless). amplitude + offset should be in range [0 to 1].
            epsilon (float): Amplitude added to the Q channel.
            delta (float): Dephasing.
        """

        frequency: float
        epsilon: float
        delta: float
        offset_i: float
        offset_q: float

    settings: AWGSettings

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path) -> QbloxResult:
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """

    @property
    def frequency(self):
        """QbloxPulsar 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency
