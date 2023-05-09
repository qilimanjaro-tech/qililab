""" Typings from AWG Types """

from enum import Enum


class AWGTypes(Enum):
    """Typings from AWG Types"""

    AWG_SEQUENCERS = "awg_sequencers"
    OUT_OFFSETS = "out_offsets"


class AWGSequencerTypes(Enum):
    """Types from AWG Sequencer Types"""

    IDENTIFIER = "identifier"
    INTERMEDIATE_FREQUENCY = "intermediate_frequency"
    OFFSET_PATH0 = "offset_path0"
    OFFSET_PATH1 = "offset_path1"
    CHIP_PORT_ID = "chip_port_id"


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
