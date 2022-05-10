"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass
from typing import List

from qililab.instruments.instrument import Instrument
from qililab.pulse import Pulse
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

        hardware_average: int
        software_average: int
        repetition_duration: int  # ns
        frequency: float
        offset_i: float
        offset_q: float
        epsilon: float
        delta: float

    settings: QubitInstrumentSettings

    @abstractmethod
    def run(self, pulses: List[Pulse]) -> QbloxResult:
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """

    @property
    def hardware_average(self):
        """QbloxPulsar 'hardware_average' property.

        Returns:
            int: settings.hardware_average.
        """
        return self.settings.hardware_average

    @property
    def software_average(self):
        """QbloxPulsar 'software_average' property.

        Returns:
            int: settings.software_average.
        """
        return self.settings.software_average

    @property
    def repetition_duration(self):
        """QbloxPulsar 'repetition_duration' property.

        Returns:
            int: settings.repetition_duration.
        """
        return self.settings.repetition_duration

    @property
    def frequency(self):
        """QbloxPulsar 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency
