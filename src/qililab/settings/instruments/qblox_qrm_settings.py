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
from enum import Enum

from pydantic import Field, model_validator

from qililab.settings.instruments.qblox_qcm_settings import QbloxModuleSettings, QbloxSequencerSettings


class AcquireTriggerMode(str, Enum):
    SEQUENCER = "sequencer"
    LEVEL = "level"


class QbloxADCSequencerSettings(QbloxSequencerSettings):
    hardware_demodulation: bool = Field(default=True)
    integration_length: int = Field(
        default=1000,
        ge=4,
        le=16777212,
        multiple_of=4,
        description="Integration length in number of samples for non-weighed acquisitions on paths 0 and 1.",
    )
    threshold: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Sequencer discretization threshold for discretizing the phase rotation result.",
    )
    threshold_rotation: float = Field(
        default=0.0, ge=0, le=360, description="Integration result phase rotation in degrees."
    )
    time_of_flight: int = Field(default=0)


class QbloxQRMSettings(QbloxModuleSettings[QbloxADCSequencerSettings]):
    scope_hardware_averaging: bool = Field(default=True)

    @model_validator(mode="after")
    def validate_outputs(self):
        for sequencer in self.sequencers:
            if not sequencer.outputs or len(sequencer.outputs) > 2:
                raise ValueError("Sequencer outputs for Qblox QRM should have length 1 or 2.")
            if any(output not in {0, 1} for output in sequencer.outputs):
                raise ValueError("Sequencer outputs for Qblox QRM should be one of {0, 1}.")
        return self


class QbloxQRMRFSettings(QbloxQRMSettings):
    output_offsets: None = Field(default=None, exclude=True)  # type: ignore[assignment]
    out0_in0_lo_frequency: float = Field(default=2e9)
    out0_in0_lo_enabled: bool = Field(default=True)
    out0_attenuation: int = Field(default=0, multiple_of=2)
    in0_attenuation: int = Field(default=0, multiple_of=2)
    out0_offset_path0: float = Field(default=0.0)
    out0_offset_path1: float = Field(default=0.0)

    @model_validator(mode="after")
    def validate_outputs(self):
        for sequencer in self.sequencers:
            if not sequencer.outputs or len(sequencer.outputs) != 1:
                raise ValueError("Sequencer outputs for Qblox QRM-RF should have length 1.")
            if any(output not in {0} for output in sequencer.outputs):
                raise ValueError("Sequencer outputs for Qblox QRM-RF should be one of {0}.")
        return self


# Remove 'offsets' from __annotations__ and model_fields
del QbloxQRMRFSettings.__annotations__["output_offsets"]
del QbloxQRMRFSettings.model_fields["output_offsets"]

# Rebuild the model to apply changes
QbloxQRMRFSettings.model_rebuild()
