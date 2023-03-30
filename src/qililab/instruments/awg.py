"""QubitControl class."""
from abc import abstractmethod
from dataclasses import asdict, dataclass
from typing import List, Sequence

from qililab.constants import RUNCARD
from qililab.instruments.awg_settings.awg_iq_channel import AWGIQChannel
from qililab.instruments.awg_settings.awg_sequencer import AWGSequencer
from qililab.instruments.awg_settings.typings import AWGSequencerPathIdentifier, AWGTypes
from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseBusSchedule
from qililab.utils.asdict_factory import dict_factory


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass(kw_only=True)
    class AWGSettings(Instrument.InstrumentSettings):
        """Contains the settings of a AWG.

        Args:
            num_sequencers (int): Number of sequencers (physical I/Q pairs)
            awg_sequencers (Sequence[AWGSequencer]): Properties of each AWG sequencer
            awg_iq_channels (list[AWGIQChannel]): Properties of each AWG IQ channel
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
    def compile(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int) -> None:
        """Compiles the ``PulseBusSchedule`` into an assembly program.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
        """

    @abstractmethod
    def run(self):
        """Run the uploaded program"""

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

    def offset_i(self, sequencer_id: int):
        """AWG 'offset_i' property."""

        path_id = self.get_sequencer_path_id_mapped_to_i_channel(sequencer_id=sequencer_id)
        if path_id == AWGSequencerPathIdentifier.PATH0:
            return self.awg_sequencers[sequencer_id].offset_path0
        return self.awg_sequencers[sequencer_id].offset_path1

    def offset_q(self, sequencer_id: int):
        """AWG 'offset_q' property."""

        path_id = self.get_sequencer_path_id_mapped_to_q_channel(sequencer_id=sequencer_id)
        if path_id == AWGSequencerPathIdentifier.PATH1:
            return self.awg_sequencers[sequencer_id].offset_path1
        return self.awg_sequencers[sequencer_id].offset_path0

    def get_sequencer_path_id_mapped_to_i_channel(self, sequencer_id: int) -> AWGSequencerPathIdentifier:
        """get sequencer path id mapped to i channel of sequencer Id

        Args:
            sequencer_id (int): sequencer identifier

        Returns:
            AWGSequencerPathIdentifier: path identifier
        """
        path_identifier = [
            iq_channel.sequencer_path_i_channel
            for iq_channel in self.awg_iq_channels
            if iq_channel.sequencer_id_i_channel == sequencer_id
        ]

        if len(path_identifier) != 1:
            raise ValueError(
                "Each sequencer should only contain 1 path connected to the I channel."
                f"Sequencer {sequencer_id} has {len(path_identifier)} paths connected to the I channel."
            )

        return path_identifier[0]

    def get_sequencer_path_id_mapped_to_q_channel(self, sequencer_id: int) -> AWGSequencerPathIdentifier:
        """get sequencer path id mapped to q channel of sequencer Id

        Args:
            sequencer_id (int): sequencer identifier

        Returns:
            AWGSequencerPathIdentifier: path identifier
        """
        path_identifier: list[AWGSequencerPathIdentifier] = [
            iq_channel.sequencer_path_q_channel
            for iq_channel in self.awg_iq_channels
            if iq_channel.sequencer_id_q_channel == sequencer_id
        ]

        if len(path_identifier) != 1:
            raise ValueError(
                "Each sequencer should only contain 1 path connected to the Q channel."
                f"Sequencer {sequencer_id} has {len(path_identifier)} paths connected to the Q channel."
            )

        return path_identifier[0]

    def to_dict(self):
        """Return a dict representation of an AWG instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()

    def get_sequencers_from_chip_port_id(self, chip_port_id: int) -> List[int]:
        """Get sequencer ids from the chip port identifier

        Args:
            chip_port_id (int): chip port identifier

        Returns:
            List[int]: list of integers containing the indices of the sequencers connected to the chip port
        """
        return [sequencer.identifier for sequencer in self.awg_sequencers if sequencer.chip_port_id == chip_port_id]

    def get_sequencer(self, sequencer_id: int) -> AWGSequencer:
        """Get sequencer from the sequencer identifier

        Args:
            sequencer_id (int): sequencer identifier

        Returns:
            AWGSequencer: sequencer associated with the sequencer_id
        """
        sequencer_identifiers = [
            sequencer.identifier for sequencer in self.awg_sequencers if sequencer.identifier == sequencer_id
        ]

        if len(sequencer_identifiers) != 1:
            raise ValueError(
                f"Each sequencer should have a unique id. Found {len(sequencer_identifiers)} sequencers "
                f"with id {sequencer_id}."
            )

        return self.awg_sequencers[sequencer_identifiers[0]]
