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

""" AWG Qblox ADC Sequencer """
from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.awg_settings.awg_qblox_sequencer import AWGQbloxSequencer


@dataclass
class AWGQbloxADCSequencer(AWGQbloxSequencer, AWGADCSequencer):
    """AWG Qblox ADC Sequencer"""

    qubit: int
    weights_i: list[float]
    weights_q: list[float]
    weighed_acq_enabled: bool

    def __post_init__(self):
        self._verify_weights()

    def _verify_weights(self):
        """Verifies that the length of weights_i and weights_q are equal.

        Raises:
            IndexError: The length of weights_i and weights_q must be equal.
        """
        if len(self.weights_i) != len(self.weights_q):
            raise IndexError("The length of weights_i and weights_q must be equal.")

    @property
    def used_integration_length(self) -> int:
        """Final integration length used by the AWG in the integration.

        Returns:
            int: Length of the weights if weighed acquisition is enabled, configured `integration_length` if disabled.
        """
        return len(self.weights_i) if self.weighed_acq_enabled else self.integration_length
