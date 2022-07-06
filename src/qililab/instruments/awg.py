"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseSequence


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass(kw_only=True)
    class AWGSettings(Instrument.InstrumentSettings):
        """Contains the settings of a AWG.

        Args:
            frequency (float): Intermediate frequency (IF).
            gain (float): Gain step used by the sequencer.
            offset_i (float): I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (float): Q offset (unitless). amplitude + offset should be in range [0 to 1].
            epsilon (float): Amplitude added to the Q channel.
            delta (float): Dephasing.
        """

        frequency: float
        num_sequencers: int
        gain: List[float]
        epsilon: List[float]
        delta: List[float]
        offset_i: List[float]
        offset_q: List[float]
        multiplexing_frequencies: List[float] = field(default_factory=list)

        def __post_init__(self):
            """Set the multiplexing_frequencies to the intermediate frequency by default."""
            super().__post_init__()
            if not self.multiplexing_frequencies:
                self.multiplexing_frequencies = [self.frequency]

    settings: AWGSettings

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
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

    @property
    def num_sequencers(self):
        """QbloxPulsar 'sequencer' property.

        Returns:
            int: settings.sequencer.
        """
        return self.settings.num_sequencers

    @property
    def gain(self):
        """QbloxPulsar 'gain' property.

        Returns:
            float: settings.gain.
        """
        return self.settings.gain

    @property
    def offset_i(self):
        """QbloxPulsar 'offset_i' property.

        Returns:
            float: settings.offset_i
        """
        return self.settings.offset_i

    @property
    def offset_q(self):
        """QbloxPulsar 'offset_q' property.

        Returns:
            float: settings.offset_q.
        """
        return self.settings.offset_q

    @property
    def epsilon(self):
        """QbloxPulsar 'epsilon' property.

        Returns:
            float: settings.epsilon.
        """
        return self.settings.epsilon

    @property
    def delta(self):
        """QbloxPulsar 'delta' property.

        Returns:
            float: settings.delta.
        """
        return self.settings.delta

    @property
    def multiplexing_frequencies(self):
        """QbloxPulsar 'multiplexing_frequencies' property.

        Returns:
            float: settings.multiplexing_frequencies.
        """
        return self.settings.multiplexing_frequencies

    @multiplexing_frequencies.setter
    def multiplexing_frequencies(self, frequencies: List[float]):
        """QbloxPulsar 'multiplexing_frequencies' property setter."""
        self.settings.multiplexing_frequencies = frequencies
