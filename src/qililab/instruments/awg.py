# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""QubitControl class."""
from abc import abstractmethod
from dataclasses import asdict, dataclass
from typing import Sequence

from qpysequence import Sequence as QpySequence

from qililab.constants import RUNCARD
from qililab.instruments.awg_settings.awg_sequencer import AWGSequencer
from qililab.instruments.awg_settings.typings import AWGTypes
from qililab.instruments.instrument import Instrument
from qililab.utils.asdict_factory import dict_factory


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass(kw_only=True)
    class AWGSettings(Instrument.InstrumentSettings):
        """Contains the settings of a AWG.

        Args:
            awg_sequencers (Sequence[AWGSequencer]): Properties of each AWG sequencer
        """

        awg_sequencers: Sequence[AWGSequencer]

        def __post_init__(self):
            """build AWGSequencers and IQ channels"""
            super().__post_init__()
            num_sequencers = len(self.awg_sequencers)
            if num_sequencers <= 0:
                raise ValueError(f"The number of sequencers must be greater than 0. Received: {num_sequencers}")
            self.awg_sequencers = [
                AWGSequencer(**sequencer) if isinstance(sequencer, dict) else sequencer  # pylint: disable=not-a-mapping
                for sequencer in self.awg_sequencers
            ]

        def to_dict(self):
            """Return a dict representation of an AWG instrument."""
            result = asdict(self, dict_factory=dict_factory)
            result.pop(AWGTypes.AWG_SEQUENCERS.value)

            return result | {AWGTypes.AWG_SEQUENCERS.value: [sequencer.to_dict() for sequencer in self.awg_sequencers]}

    settings: AWGSettings

    @abstractmethod
    def run(self, channel_id: int | str | None):
        """Run the uploaded program"""

    @abstractmethod
    def upload(self, channel_id: int | str | None):
        """Upload compiled program."""

    @abstractmethod
    def upload_qpysequence(self, qpysequence: QpySequence, channel_id: int | str | None):
        """Upload qpysequence."""

    @property
    def num_sequencers(self):
        """Number of sequencers in the AWG

        Returns:
            int: number of sequencers
        """
        return len(self.settings.awg_sequencers)

    @property
    def awg_sequencers(self):
        """AWG 'awg_sequencers' property."""
        return self.settings.awg_sequencers

    @property
    def intermediate_frequencies(self):
        """AWG 'intermediate_frequencies' property."""
        return [sequencer.intermediate_frequency for sequencer in self.awg_sequencers]

    def to_dict(self):
        """Return a dict representation of an AWG instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()

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
