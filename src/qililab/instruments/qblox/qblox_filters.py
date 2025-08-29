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
from qililab.constants import DistortionState
from typing import Sequence

@dataclass
class QbloxFilter:
    module: int | None = None
    exponential_amplitude: float | None = None
    exponential_tau: float | None = None
    exponential_state: DistortionState = None
    fir_coeff: Sequence | None = None
    fir_state: DistortionState | None = None

    def to_dict(self):
        """Return a dict representation of a Qblox Filter."""
        return asdict(self, dict_factory=dict_factory)
