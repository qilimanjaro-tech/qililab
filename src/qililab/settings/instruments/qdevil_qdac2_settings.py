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

from qililab.settings.instruments.channel_settings import ChannelSettings
from qililab.settings.instruments.instrument_settings import InstrumentWithChannelsSettings


class QDevilQDAC2Span(str, Enum):
    LOW = "low"
    HIGH = "high"


class QDevilQDAC2LowPassFilter(str, Enum):
    DC = "dc"
    MEDIUM = "medium"
    HIGH = "high"


class QDevilQDAC2ChannelSettings(ChannelSettings[int]):
    voltage: float = Field(default=0.0, ge=-10.0, le=10.0, description="Voltage in V.")
    span: QDevilQDAC2Span = Field(default=QDevilQDAC2Span.LOW, description="Voltage range.")
    ramping_enabled: bool = Field(default=True)
    ramping_rate: float = Field(default=1.0, ge=0.01, le=2e7, description="Ramping rate of voltage change in V/s.")
    low_pass_filter: QDevilQDAC2LowPassFilter = Field(default=QDevilQDAC2LowPassFilter.DC)

    @model_validator(mode="after")
    def validate_voltage(self):
        if self.span == QDevilQDAC2Span.LOW and (self.voltage < -2.0 or self.voltage > 2.0):
            raise ValueError("Voltage should be in the range [-2, 2]V if span is set to `low`.")
        return self


class QDevilQDAC2Settings(InstrumentWithChannelsSettings[QDevilQDAC2ChannelSettings, int]):
    @model_validator(mode="after")
    def validate_dacs(self):
        if len(self.channels) > 24:
            raise ValueError("The maximum number of dacs is 24.")
        return self
