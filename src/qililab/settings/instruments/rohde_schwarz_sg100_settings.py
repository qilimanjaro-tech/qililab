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

from pydantic import Field

from qililab.settings.instruments.instrument_settings import InstrumentSettings


class RohdeSchwarzSG100Settings(InstrumentSettings):
    power: float = Field(..., gt=-30.0, lt=20.0, description="Power in dBm.")
    frequency: float = Field(..., gt=1e6, lt=20e9, description="Frequency in Hz.")
    rf_on: bool = Field(default=False)
