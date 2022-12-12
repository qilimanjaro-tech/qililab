""" AWG Channel Mapping """


from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_sequencer_path import (
    AWGSequencerPathIdentifier,
)


@dataclass
class AWGChannelMapping:
    """AWG Channel Mapping"""

    awg_sequencer_identifier: int
    awg_sequencer_path_identifier: AWGSequencerPathIdentifier
