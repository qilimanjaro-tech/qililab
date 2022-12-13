""" Typings from AWG Types """

from enum import Enum


class AWGSequencerTypes(Enum):
    """Types from AWG Sequencer Types"""

    IDENTIFIER = "identifier"
    PATH0 = "path0"
    PATH1 = "path1"
    INTERMEDIATE_FREQUENCY = "intermediate_frequency"
    OFFSET_PATH0 = "offset_path0"
    OFFSET_PATH1 = "offset_path1"


class AWGSequencerPathIdentifier(Enum):
    """AWG Sequence Path Identifier
    Options:
        PATH0 = 0
        PATH1 = 1
    """

    PATH0 = 0
    PATH1 = 1


class AWGSequencerPathTypes(Enum):
    """Types from AWG Sequencer Path Types"""

    PATH_ID = "path_id"
    OUTPUT_CHANNEL = "output_channel"


class AWGIQChannelTypes(Enum):
    """Types from AWG IQ Channel Types"""

    IDENTIFIER = "identifier"
    I_CHANNEL = "i_channel"
    Q_CHANNEL = "q_channel"


class AWGChannelMappingTypes(Enum):
    """Types from AWG Channel Mapping Types"""

    AWG_SEQUENCER_IDENTIFIER = "awg_sequencer_identifier"
    AWG_SEQUENCER_PATH_IDENTIFIER = "awg_sequencer_path_identifier"


class AWGOutputChannelTypes(Enum):
    """Types from AWG Ouput Channel Types"""

    IDENTIFIER = "identifier"
