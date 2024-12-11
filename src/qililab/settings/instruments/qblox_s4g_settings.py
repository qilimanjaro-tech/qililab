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


class QbloxS4gSpan(str, Enum):
    MIN_BI = "min_bi"
    MAX_BI = "max_bi"
    MAX_UNI = "max_uni"


class QbloxS4GChannelSettings(ChannelSettings[int]):
    current: float = Field(default=0.0, ge=-0.04, le=0.04, description="Output current of the dac channel in A.")
    span: QbloxS4gSpan = Field(default=QbloxS4gSpan.MIN_BI, description="Current range of the dacs.")
    ramping_enabled: bool = Field(default=True)
    ramping_rate: float = Field(default=1e-3, description="Ramping rate of current change in A/s.")

    @model_validator(mode="after")
    def validate_current(self):
        if self.span == QbloxS4gSpan.MIN_BI and (self.current < -0.02 or self.current > 0.02):
            raise ValueError("current should be in the range [-0.02, 0.02]A if span is set to `min_bi`.")
        if self.span == QbloxS4gSpan.MAX_UNI and (self.current < 0.0):
            raise ValueError("current should be in the range [0.0, 0.04]A if span is set to `max_uni`.")
        return self


class QbloxS4GSettings(InstrumentWithChannelsSettings[ChannelSettings, int]):
    @model_validator(mode="after")
    def validate_dacs(self):
        if len(self.channels) > 4:
            raise ValueError("The maximum number of dacs is 4.")
        return self
