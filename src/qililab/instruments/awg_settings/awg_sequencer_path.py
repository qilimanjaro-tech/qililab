""" AWG Sequencer Path """


from dataclasses import dataclass
from enum import Enum

from qililab.instruments.awg_settings.awg_output_channel import AWGOutputChannel


class AWGSequencerPathIdentifier(Enum):
    """AWG Sequence Path Identifier
    Options:
        PATH0 = 0
        PATH1 = 1
    """

    PATH0 = 0
    PATH1 = 1


@dataclass
class AWGSequencerPath:
    """AWG Channel Mapping"""

    path_id: AWGSequencerPathIdentifier
    output_channel: AWGOutputChannel
