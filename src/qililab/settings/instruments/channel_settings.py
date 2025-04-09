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

from pydantic import BaseModel

from qililab.settings.settings import Settings

ChannelID = TypeVar("ChannelID", int, str)


class ChannelSettings(Settings, Generic[ChannelID]):
    id: ChannelID


class ModulatedMixin(BaseModel):
    intermediate_frequency: float


class ToSingleOutputMixin(BaseModel):
    output: int


class ToIQOutputMixin(BaseModel):
    output_i: int
    output_q: int


class FromSingleInputMixin(BaseModel):
    input: int


class FromIQInputMixin(BaseModel):
    input_i: int
    input_q: int
