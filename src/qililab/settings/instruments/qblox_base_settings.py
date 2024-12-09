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

from pydantic import Field

from qililab.settings.instruments.channel_settings import ChannelSettings
from qililab.settings.instruments.input_settings import InputSettings
from qililab.settings.instruments.instrument_settings import InstrumentWithChannelsSettings
from qililab.settings.instruments.output_settings import OutputSettings


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


class QbloxADCSequencerSettings(QbloxSequencerSettings):
    inputs: list[int] = Field(default=[0])
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


class QbloxOutputSettings(OutputSettings):
    pass


class QbloxLFOutputSettings(QbloxOutputSettings):
    offset: float = Field(default=0.0, ge=-2.5, le=2.5, description="Output offset in V.")


class QbloxRFOutputSettings(QbloxOutputSettings):
    lo_enabled: bool = Field(default=True, description="Output local oscillator enabled flag.")
    lo_frequency: float = Field(default=10e9, ge=2e9, le=18e9, description="Local oscillator frequency in Hz.")
    attenuation: int = Field(
        default=0,
        ge=0,
        le=60,
        multiple_of=2,
        description="Output attenuation in a range of 0dB to 60dB with a resolution of 2dB per step.",
    )
    offset_i: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output offset for I in mV.")
    offset_q: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output offset for Q in mV.")


class QbloxInputSettings(InputSettings):
    pass


class QbloxLFInputSettings(QbloxInputSettings):
    gain: int = Field(
        default=0, ge=-6, le=26, description="Input gain in a range of -6dB to 26dB with a resolution of 1dB per step."
    )
    offset: float = Field(default=0, ge=-0.09, le=0.09, description="Input offset in a range of -0.09V to 0.09V")


class QbloxRFInputSettings(QbloxInputSettings):
    attenuation: int = Field(
        default=0,
        ge=0,
        le=30,
        multiple_of=2,
        description="Input attenuation in a range of 0dB to 30dB with a resolution of 2dB per step.",
    )
    offset_i: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output offset for I in mV.")
    offset_q: float = Field(default=0.0, ge=-84.0, le=73.0, description="Output offset for Q in mV.")


TSequencer = TypeVar("TSequencer", bound=QbloxSequencerSettings)
TOutput = TypeVar("TOutput", bound=QbloxOutputSettings)
TInput = TypeVar("TInput", bound=QbloxInputSettings)


class QbloxModuleSettings(InstrumentWithChannelsSettings[TSequencer, int], Generic[TSequencer, TOutput]):
    timeout: int = Field(default=1)
    outputs: list[TOutput]


class QbloxControlModuleSettings(QbloxModuleSettings[QbloxSequencerSettings, TOutput], Generic[TOutput]):
    pass


class QbloxReadoutModuleSettings(QbloxModuleSettings[QbloxADCSequencerSettings, TOutput], Generic[TOutput, TInput]):
    inputs: list[TInput]
    scope_hardware_averaging: bool = Field(default=True)
