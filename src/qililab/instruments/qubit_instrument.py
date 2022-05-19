"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseSequence
from qililab.result import QbloxResult


class QubitInstrument(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass
    class QubitInstrumentSettings(Instrument.InstrumentSettings):
        """Contains the settings of a QubitInstrument.

        Args:
            hardware_average (int): Hardware average. Number of shots used when executing a sequence.
            software_average (int): Software average.
            repetition_duration (int): Duration (ns) of the whole program.
            offset_i (float): I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (float): Q offset (unitless). amplitude + offset should be in range [0 to 1].
            epsilon (float): Amplitude added to the Q channel.
            delta (float): Dephasing.
        """

        frequency: float
        offset_i: float
        offset_q: float
        epsilon: float
        delta: float

    settings: QubitInstrumentSettings

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence, nshots: int, loop_duration: int) -> QbloxResult:
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
