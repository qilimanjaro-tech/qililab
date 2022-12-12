"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from qililab.instruments.awg_settings.awg_iq_channel import AWGIQChannel
from qililab.instruments.awg_settings.awg_output_channel import AWGOutputChannel
from qililab.instruments.awg_settings.awg_sequencer import AWGSequencer
from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseBusSchedule


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass(kw_only=True)
    class AWGSettings(Instrument.InstrumentSettings):
        """Contains the settings of a AWG.

        Args:
            num_sequencers (int): Number of sequencers (physical I/Q pairs)
            sequencers (list[AWGSequencer]): Properties of each AWG sequencer
        """

        num_sequencers: int
        awg_sequencers: list[AWGSequencer]
        awg_iq_channels: list[AWGIQChannel]

        def __post_init__(self):
            """build AWGSequencers and IQ channels"""
            super().__post_init__()
            if self.num_sequencers <= 0:
                raise ValueError(f"The number of sequencers must be greater than 0. Received: {self.num_sequencers}")
            if len(self.awg_sequencers) != self.num_sequencers:
                raise ValueError(
                    f"The number of sequencers: {self.num_sequencers} does not match"
                    + f" the number of AWG Sequencers settings specified: {len(self.awg_sequencers)}"
                )
            self.awg_sequencers = [
                AWGSequencer.from_dict(sequencer) if isinstance(sequencer, dict) else sequencer
                for sequencer in self.awg_sequencers
            ]
            self.awg_iq_channels = [
                AWGIQChannel.from_dict(iq_channel) if isinstance(iq_channel, dict) else iq_channel
                for iq_channel in self.awg_iq_channels
            ]

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
        """AWG 'frequency' property."""
        # FIXME: this must be deleted, as an AWG has a frequency for each channel.
        # Returning the first frequency for now.
        return self.intermediate_frequencies[0]

    @property
    def num_sequencers(self):
        """Number of sequencers in the AWG

        Returns:
            int: number of sequencers
        """
        return self.settings.num_sequencers

    @property
    def awg_sequencers(self):
        """AWG 'awg_sequencers' property."""
        return self.settings.awg_sequencers

    @property
    def awg_iq_channels(self):
        """AWG 'awg_iq_channels' property."""
        return self.settings.awg_iq_channels

    @property
    def intermediate_frequencies(self):
        """AWG 'intermediate_frequencies' property."""
        return [
            self.settings.awg_sequencers[sequencer.identifier].intermediate_frequency
            for sequencer in self.awg_sequencers
        ]
