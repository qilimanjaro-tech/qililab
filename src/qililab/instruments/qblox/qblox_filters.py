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

from qililab.constants import QBLOXCONSTANTS
from qililab.typings import DistortionState
from qililab.utils.asdict_factory import dict_factory


@dataclass
class QbloxFilter:
    """Defines exponential and FIR filter settings for Qblox outputs.

    Attributes:
        output_id (int | None): Output channel identifier.
        exponential_amplitude (list | None): Amplitude values for exponential filters (up to 4). Scalars or shorter lists are expanded to length 4.
        exponential_time_constant (list | None): Time constants for exponential filters (up to 4). Scalars or shorter lists are expanded to length 4.
        exponential_state (list | None): States for exponential filters. True is converted to DistortionState.ENABLED and False to DistortionState.BYPASSED. Scalars or shorter lists are expanded to length 4.
        fir_coeff (list | None): FIR coefficients (must be exactly 32 if provided). Raises ValueError if length is not 32.
        fir_state (bool | DistortionState | str | None): FIR filter state. True is converted to DistortionState.ENABLED and False to DistortionState.BYPASSED.
    """

    output_id: int | None = None
    exponential_amplitude: list | None = None
    exponential_time_constant: list | None = None
    exponential_state: list | None = None
    fir_coeff: list | None = None
    fir_state: bool | DistortionState | str | None = None

    def __post_init__(self):
        if isinstance(self.exponential_state, (bool, str)):
            self.exponential_state = [self.exponential_state]

        if isinstance(self.exponential_time_constant, (int, float)):
            self.exponential_time_constant = [self.exponential_time_constant]

        if isinstance(self.exponential_amplitude, (int, float)):
            self.exponential_amplitude = [self.exponential_amplitude]

        if self.exponential_state is not None:
            for idx, state in enumerate(self.exponential_state):
                if state is True:
                    self.exponential_state[idx] = DistortionState.ENABLED.value
                elif state is False:
                    self.exponential_state[idx] = DistortionState.BYPASSED.value
            self.exponential_state = self.exponential_state + [None] * (4 - len(self.exponential_state))

        if self.exponential_time_constant is not None:
            self.exponential_time_constant = self.exponential_time_constant + [None] * (
                4 - len(self.exponential_time_constant)
            )

        if self.exponential_amplitude is not None:
            self.exponential_amplitude = self.exponential_amplitude + [None] * (4 - len(self.exponential_amplitude))

        if self.fir_state is True:
            self.fir_state = DistortionState.ENABLED.value
        elif self.fir_state is False:
            self.fir_state = DistortionState.BYPASSED.value

        if self.fir_coeff is not None and len(self.fir_coeff) != QBLOXCONSTANTS.FILTER_FIR_COEFF_LENGTH:
            raise ValueError(
                f"The number of elements in the list must be exactly {QBLOXCONSTANTS.FILTER_FIR_COEFF_LENGTH}. Received: {len(self.fir_coeff)}"
            )

    def to_dict(self):
        """Return a dict representation of a Qblox Filter."""
        return asdict(self, dict_factory=dict_factory)
