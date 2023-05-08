""" AWG Sequencer Path """


from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_output_channel import AWGOutputChannel
from qililab.instruments.awg_settings.typings import AWGSequencerPathIdentifier, AWGSequencerPathTypes


@dataclass
class AWGSequencerPath:
    """AWG Channel Mapping"""

    path_id: AWGSequencerPathIdentifier
    output_channel: AWGOutputChannel

    def __post_init__(self):
        """Build AWGSequencerPath"""
        if isinstance(self.path_id, int):
            self.path_id = AWGSequencerPathIdentifier(self.path_id)
        if isinstance(self.output_channel, int):
            self.output_channel = AWGOutputChannel(self.output_channel)

    def to_dict(self):
        """Return a dict representation of an AWG Sequencer Path."""
        return {AWGSequencerPathTypes.OUTPUT_CHANNEL.value: self.output_channel.identifier}
