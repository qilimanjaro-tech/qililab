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

from dataclasses import asdict, dataclass

from qililab.utils.asdict_factory import dict_factory


@dataclass
class QbloxSequencer:
    identifier: int
    outputs: list[int]  # [3, 2] means I path is connected to output 3 and Q path is connected to output 2
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
