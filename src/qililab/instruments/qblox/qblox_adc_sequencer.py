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

import warnings
from dataclasses import dataclass

from qililab.instruments.qblox.qblox_sequencer import QbloxSequencer
from qililab.typings import AcquireTriggerMode, IntegrationMode
from qililab.utils.castings import cast_enum_fields


@dataclass
class QbloxADCSequencer(QbloxSequencer):
    scope_acquire_trigger_mode: AcquireTriggerMode
    scope_hardware_averaging: bool
    # default sampling rate for Qblox is 1.e+09
    sampling_rate: float
    # demodulation flag
    hardware_demodulation: bool
    integration_mode: IntegrationMode
    # minutes
    acquisition_timeout: int
    scope_store_enabled: bool
    threshold: float
    threshold_rotation: float
    # nanoseconds
    time_of_flight: int
    integration_length: int | None = None
    # minutes
    sequence_timeout: int | None = None
    timeout_repetitions: int = 0

    def __post_init__(self):
        cast_enum_fields(obj=self)
        if self.integration_length is not None:
            warnings.warn(
                "Integration_length in the runcard is deprecated and will be removed in a future release. "
                "The integration length is now derived from the QProgram's first weight duration.",
                FutureWarning,
                stacklevel=1,
            )
        if self.sequence_timeout is not None:
            warnings.warn(
                "sequence_timeout in the runcard is deprecated and will be removed in a future release. "
                "It has no effect on the instrument's behavior.",
                FutureWarning,
                stacklevel=1,
            )
