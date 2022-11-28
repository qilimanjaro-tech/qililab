"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseBusSchedule


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass(kw_only=True)
    class AWGSettings(Instrument.InstrumentSettings):
        """Contains the settings of a AWG.

        Args:
            num_sequencers (int): Number of sequencers (physical I/Q pairs)
            frequencies (List[float]): Frequency for each sequencer
            gain (List[float]): Gain step used by the sequencer.
            gain_imbalance (float): Amplitude added to the Q channel.
            phase_imbalance (float): Dephasing.
            delta (List[float]): Dephasing.
            offset_i (List[float]): I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (List[float]): Q offset (unitless). amplitude + offset should be in range [0 to 1].
            hardware_modulation (List[bool]): Flag to determine if the modulation of a specific channel is performed by the device
        """

        num_sequencers: int
        frequencies: List[float]
        gain: List[float]
        gain_imbalance: List[float]
        phase_imbalance: List[float]
        offset_i: List[float]
        offset_q: List[float]
        hardware_modulation: List[bool]

    settings: AWGSettings

    @abstractmethod
    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetitition duration
            path (Path): path to save the program to upload
        """

    @abstractmethod
    def run(self):
        """Run the uploaded program"""

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
    def gain_imbalance(self):
        """QbloxPulsar 'gain_imbalance' property.

        Returns:
            float: settings.gain_imbalance.
        """
        return self.settings.gain_imbalance

    @property
    def phase_imbalance(self):
        """QbloxPulsar 'phase_imbalance' property.

        Returns:
            float: settings.phase_imbalance.
        """
        return self.settings.phase_imbalance

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
