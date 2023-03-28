""" AWG Channel Mapping """


from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_sequencer_path import AWGSequencerPathIdentifier
from qililab.instruments.awg_settings.typings import AWGChannelMappingTypes


@dataclass
class AWGChannelMapping:
    """AWG Channel Mapping"""

    awg_sequencer_identifier: int
    awg_sequencer_path_identifier: AWGSequencerPathIdentifier

    def __post_init__(self):
        """Build AWGSequencerPathIdentifier"""
        if isinstance(self.awg_sequencer_path_identifier, int):
            self.awg_sequencer_path_identifier = AWGSequencerPathIdentifier(self.awg_sequencer_path_identifier)

    def to_dict(self):
        """Return a dict representation of an AWG IQ Channel."""
        return {
            AWGChannelMappingTypes.AWG_SEQUENCER_IDENTIFIER.value: self.awg_sequencer_identifier,
            AWGChannelMappingTypes.AWG_SEQUENCER_PATH_IDENTIFIER.value: self.awg_sequencer_path_identifier.value,
        }
