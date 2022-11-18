"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass
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
            num_sequencers (int): Number of sequencers
            frequencies (List[float]): Frequency for each sequencer
            gain (List[float]): Gain step used by the sequencer.
            epsilon (List[float]): Amplitude added to the Q channel.
            delta (List[float]): Dephasing.
            offset_i (List[float]): I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (List[float]): Q offset (unitless). amplitude + offset should be in range [0 to 1].
            hardware_modulation (List[bool]): Flag to determine if the modulation of a specific channel is performed by the device
        """

        num_sequencers: int
        frequencies: List[float]
        gain: List[float]
        epsilon: List[float]
        delta: List[float]
        offset_i: List[float]
        offset_q: List[float]
        hardware_modulation: List[bool]

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
        # FIXME: this must be deleted, as an AWG has a frequency for each channel.
        # Returning the first frequency for now.
        return self.settings.frequencies[0]

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
    def frequencies(self):
        """QbloxPulsar 'frequencies' property.

        Returns:
            float: settings.frequencies.
        """
        return self.settings.frequencies

    @frequencies.setter
    def frequencies(self, frequencies: List[float]):
        """QbloxPulsar 'frequencies' property setter."""
        self.settings.frequencies = frequencies
