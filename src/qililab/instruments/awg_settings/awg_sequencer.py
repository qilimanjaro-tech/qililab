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

""" AWG Sequencer """
from dataclasses import asdict, dataclass

from qililab.utils.asdict_factory import dict_factory


@dataclass
class AWGSequencer:  # pylint: disable=too-many-instance-attributes
    """AWG Sequencer

    Args:
        identifier (int): The identifier of the sequencer
        chip_port_id (str | None): Port identifier of the chip where a specific sequencer is connected to.
                                    By default, using the first sequencer
        outputs (list(int)): List of integers containing the outputs of the I and Q paths respectively. If the list only
            contains one item, then only one output will be connected.
        output_q (int): AWG output associated with the Q channel of the sequencer
        intermediate_frequency (float): Frequency for each sequencer
        gain_imbalance (float): Amplitude added to the Q channel.
        phase_imbalance (float): Dephasing.
        hardware_modulation  (bool): Flag to determine if the modulation is performed by the device
        gain_i (float): Gain step used by the I channel of the sequencer.
        gain_q (float): Gain step used by the Q channel of the sequencer.
        offset_i (float): I offset (unitless). amplitude + offset should be in range [0 to 1].
        offset_q (float): Q offset (unitless). amplitude + offset should be in range [0 to 1].
    """

    identifier: int
    chip_port_id: str | None
    # list containing the outputs for the I and Q paths e.g. [3, 2] means I path is connected to output 3 and Q path is connected to output 2
    outputs: list[int]
    intermediate_frequency: float
    gain_imbalance: float | None
    phase_imbalance: float | None
    hardware_modulation: bool
    gain_i: float
    gain_q: float
    offset_i: float
    offset_q: float

    def to_dict(self):
        """Return a dict representation of an AWG Sequencer."""
        return asdict(self, dict_factory=dict_factory) | {"outputs": self.outputs}
