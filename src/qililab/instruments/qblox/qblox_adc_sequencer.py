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

from dataclasses import dataclass

from qililab.instruments.qblox.qblox_sequencer import QbloxSequencer
from qililab.typings import AcquireTriggerMode, IntegrationMode
from qililab.utils.castings import cast_enum_fields


@dataclass
class QbloxADCSequencer(QbloxSequencer):
    scope_acquire_trigger_mode: AcquireTriggerMode
    scope_hardware_averaging: bool
    sampling_rate: float  # default sampling rate for Qblox is 1.e+09
    hardware_demodulation: bool  # demodulation flag
    integration_length: int
    integration_mode: IntegrationMode
    sequence_timeout: int  # minutes
    acquisition_timeout: int  # minutes
    scope_store_enabled: bool
    threshold: float
    threshold_rotation: float
    time_of_flight: int  # nanoseconds

    def __post_init__(self):
        cast_enum_fields(obj=self)
