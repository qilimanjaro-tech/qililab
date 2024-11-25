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
from qililab.settings.instruments.instrument_settings import InstrumentSettings


class QbloxD5ASpan(str, Enum):
    BI_2V = "bi_2V"
    BI_4V = "bi_4V"
    BI_8V = "bi_8V"
    UNI_4V = "uni_4V"
    UNI_8V = "uni_8V"


class QbloxD5AChannelSettings(ChannelSettings[int]):
    voltage: float = Field(default=0.0, ge=-8.0, le=8.0, description="Voltage in V.")
    span: QbloxD5ASpan = Field(default=QbloxD5ASpan.BI_2V, description="Voltage range.")
    ramping_enabled: bool = Field(default=True)
    ramping_rate: float = Field(default=100e-3, description="Ramping rate of voltage change in V/s.")

    @model_validator(mode="after")
    def validate_voltage(self):
        if self.span == QbloxD5ASpan.BI_2V and (self.voltage < -2.0 or self.voltage > 2.0):
            raise ValueError("Voltage should be in the range [-2, 2]V if span is set to `bi_2V`.")
        if self.span == QbloxD5ASpan.BI_4V and (self.voltage < -4.0 or self.voltage > 4.0):
            raise ValueError("Voltage should be in the range [-4, 4]V if span is set to `bi_4V`.")
        if self.span == QbloxD5ASpan.UNI_4V and (self.voltage < 0.0 or self.voltage > 4.0):
            raise ValueError("Voltage should be in the range [0, 4]V if span is set to `uni_4V`.")
        if self.span == QbloxD5ASpan.UNI_8V and (self.voltage < 0.0):
            raise ValueError("Voltage should be in the range [0, 8]V if span is set to `uni_8V`.")
        return self


class QbloxD5ASettings(InstrumentSettings):
    dacs: list[QbloxD5AChannelSettings] = Field(default=[QbloxD5AChannelSettings(id=index) for index in range(16)])

    @model_validator(mode="after")
    def validate_dacs(self):
        if len(self.dacs) > 16:
            raise ValueError("The maximum number of dacs is 16.")
        return self
