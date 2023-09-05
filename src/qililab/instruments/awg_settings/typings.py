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
    OFFSET_I = "offset_i"
    OFFSET_Q = "offset_q"
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
