"""QubitControl class."""
from abc import abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from qililab.constants import RUNCARD
from qililab.instruments.awg_settings.awg_iq_channel import AWGIQChannel
from qililab.instruments.awg_settings.awg_sequencer import AWGSequencer
from qililab.instruments.awg_settings.typings import (
    AWGSequencerPathIdentifier,
    AWGTypes,
)
from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseBusSchedule
from qililab.typings.enums import Parameter
from qililab.utils.asdict_factory import dict_factory


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
        awg_sequencers: Sequence[AWGSequencer]
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
                AWGSequencer(**sequencer) if isinstance(sequencer, dict) else sequencer  # pylint: disable=not-a-mapping
                for sequencer in self.awg_sequencers
            ]
            self.awg_iq_channels = [
                AWGIQChannel(**iq_channel)  # pylint: disable=not-a-mapping
                if isinstance(iq_channel, dict)
                else iq_channel
                for iq_channel in self.awg_iq_channels
            ]

        def to_dict(self):
            """Return a dict representation of an AWG instrument."""
            result = asdict(self, dict_factory=dict_factory)
            result.pop(AWGTypes.AWG_SEQUENCERS.value)
            result.pop(AWGTypes.AWG_IQ_CHANNELS.value)

            return result | {
                AWGTypes.AWG_SEQUENCERS.value: [sequencer.to_dict() for sequencer in self.awg_sequencers],
                AWGTypes.AWG_IQ_CHANNELS.value: [iq_channel.to_dict() for iq_channel in self.awg_iq_channels],
            }

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

    def get_sequencer_path_id_mapped_to_i_channel(self, sequencer_id: int) -> AWGSequencerPathIdentifier:
        """get sequencer path id mapped to i channel of sequencer Id

        Args:
            sequencer_id (int): sequencer identifier

        Returns:
            AWGSequencerPathIdentifier: path identifier
        """
        path_identifier: list[AWGSequencerPathIdentifier] = list(
            filter(
                None,
                [
                    iq_channel.sequencer_path_i_channel
                    for iq_channel in self.awg_iq_channels
                    if iq_channel.sequencer_id_i_channel == sequencer_id
                ],
            )
        )
        if len(path_identifier) <= 0:
            raise ValueError(f"No I Channel mapped to the sequencer with id: {sequencer_id}")
        if len(path_identifier) > 1:
            raise ValueError(f"More than one I Channel mapped to the sequencer with id: {sequencer_id}")
        return path_identifier[0]

    def get_sequencer_path_id_mapped_to_q_channel(self, sequencer_id: int) -> AWGSequencerPathIdentifier:
        """get sequencer path id mapped to q channel of sequencer Id

        Args:
            sequencer_id (int): sequencer identifier

        Returns:
            AWGSequencerPathIdentifier: path identifier
        """
        path_identifier: list[AWGSequencerPathIdentifier] = list(
            filter(
                None,
                [
                    iq_channel.sequencer_path_q_channel
                    for iq_channel in self.awg_iq_channels
                    if iq_channel.sequencer_id_q_channel == sequencer_id
                ],
            )
        )
        if len(path_identifier) <= 0:
            raise ValueError(f"No Q Channel mapped to the sequencer with id: {sequencer_id}")
        if len(path_identifier) > 1:
            raise ValueError(f"More than one Q Channel mapped to the sequencer with id: {sequencer_id}")
        return path_identifier[0]

    def to_dict(self):
        """Return a dict representation of an AWG instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()
