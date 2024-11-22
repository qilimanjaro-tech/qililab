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
from typing import Generic, TypeVar

from pydantic import Field, model_validator

from qililab.settings.instruments.channel_settings import ChannelSettings
from qililab.settings.instruments.instrument_settings import InstrumentSettings


class QbloxSequencerSettings(ChannelSettings[int]):
    outputs: list[int] = Field(default=[0])
    hardware_modulation: bool = Field(default=True)
    intermediate_frequency: float | None = Field(default=500e6)
    gain_imbalance: float = Field(default=0.0)
    phase_imbalance: float = Field(default=0.0)
    gain_i: float = Field(default=1.0, ge=-1.0, le=1.0)
    gain_q: float = Field(default=1.0, ge=-1.0, le=1.0)
    offset_i: float = Field(default=0.0, ge=-1.0, le=1.0)
    offset_q: float = Field(default=0.0, ge=-1.0, le=1.0)


TSequencer = TypeVar("TSequencer", bound=QbloxSequencerSettings)


class QbloxModuleSettings(InstrumentSettings, Generic[TSequencer]):
    timeout: int = Field(default=1)
    output_offsets: list[float] = Field(default=[0.0, 0.0, 0.0, 0.0])
    sequencers: list[TSequencer] = Field(default=[])


class QbloxQCMSettings(QbloxModuleSettings[QbloxSequencerSettings]):
    @model_validator(mode="after")
    def validate_outputs(self):
        for sequencer in self.sequencers:
            if not sequencer.outputs or len(sequencer.outputs) > 2:
                raise ValueError("Sequencer outputs for Qblox QCM should have length 1 or 2.")
            if any(output not in {0, 1, 2, 3} for output in sequencer.outputs):
                raise ValueError("Sequencer outputs for Qblox QCM should be one of {0, 1, 2, 3}.")
        return self


class QbloxQCMRFSettings(QbloxQCMSettings):
    output_offsets: None = Field(default=None, exclude=True)  # type: ignore[assignment]
    out0_lo_frequency: float = Field(
        default=2e9, ge=2e9, le=18e9, description="Output 1 local oscillator frequency in Hz."
    )
    out0_lo_enabled: bool = Field(default=True, description="Output 0 local oscillator enabled.")
    out0_attenuation: int = Field(
        default=0,
        ge=0,
        le=60,
        multiple_of=2,
        description="Output 0 attenuation in a range of 0 dB to 60 dB with a resolution of 2dB per step.",
    )
    out0_offset_path0: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output 0 offset for path 0 in mV.")
    out0_offset_path1: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output 0 offset for path 1 in mV.")
    out1_lo_frequency: float = Field(
        default=2e9, ge=2e9, le=18e9, description="Output 1 local oscillator frequency in Hz."
    )
    out1_lo_enabled: bool = Field(default=True, description="Output 0 local oscillator enabled.")
    out1_attenuation: int = Field(
        default=0,
        multiple_of=2,
        description="Output 1 attenuation in a range of 0 dB to 60 dB with a resolution of 2dB per step.",
    )
    out1_offset_path0: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output 1 offset for path 0 in mV.")
    out1_offset_path1: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output 1 offset for path 1 in mV.")

    @model_validator(mode="after")
    def validate_outputs(self):
        for sequencer in self.sequencers:
            if not sequencer.outputs or len(sequencer.outputs) != 1:
                raise ValueError("Sequencer outputs for Qblox QCM-RF should have length 1.")
            if any(output not in {0, 1} for output in sequencer.outputs):
                raise ValueError("Sequencer outputs for Qblox QCM-RF should be one of {0, 1}.")
        return self


# Remove 'offsets' from __annotations__ and model_fields
del QbloxQCMRFSettings.__annotations__["output_offsets"]
del QbloxQCMRFSettings.model_fields["output_offsets"]

# del QbloxQCMRFSettings.model_validators['output_offsets']

# Rebuild the model to apply changes
QbloxQCMRFSettings.model_rebuild()
