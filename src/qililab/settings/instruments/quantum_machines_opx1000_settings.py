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

from pydantic import BaseModel

from qililab.settings.instruments.channel_settings import ChannelSettings


class ControllerPort(BaseModel):
    controller: str
    port: int


class OPXElement(ChannelSettings[str]):
    intermediate_frequency: float


class IQElement(OPXElement):
    I: ControllerPort
    Q: ControllerPort
    lo_frequency: float


class SingleElement(OPXElement):
    port: ControllerPort
