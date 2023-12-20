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

""" AWG ADC Sequencer """


from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_sequencer import AWGSequencer
from qililab.typings.enums import AcquireTriggerMode, IntegrationMode
from qililab.utils.castings import cast_enum_fields


@dataclass
class AWGADCSequencer(AWGSequencer):  # pylint: disable=too-many-instance-attributes
    """AWG ADC Sequencer

    Args:
        acquire_trigger_mode (str): Set scope acquisition trigger mode. Options are 'sequencer' or 'level'.
        scope_hardware_averaging (bool): Enable/disable hardware averaging of the data during scope mode.
        integration_length (int): Duration (in ns) of the integration.
        integration_mode (str): Integration mode. Options are 'ssb'.
        sequence_timeout (int): Time (in minutes) to wait for the sequence to finish.
        If timeout is reached a TimeoutError is raised.
        acquisition_timeout (int): Time (in minutes) to wait for the acquisition to finish.
        If timeout is reached a TimeoutError is raised.
    """

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

    def __post_init__(self):
        """Cast all enum attributes to its corresponding Enum class."""
        cast_enum_fields(obj=self)
