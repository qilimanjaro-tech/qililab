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
from collections.abc import Sequence
from typing import Generic

from qililab.settings.settings import Settings
from qililab.types import TChannelID, TChannelSettings


class InstrumentSettings(Settings):
    alias: str


class InstrumentWithChannelsSettings(InstrumentSettings, Generic[TChannelSettings, TChannelID]):
    channels: Sequence[TChannelSettings]

    def has_channel(self, id: TChannelID) -> bool:
        return any(channel.id == id for channel in self.channels)

    def get_channel(self, id: TChannelID) -> TChannelSettings:
        channel = next((channel for channel in self.channels if channel.id == id), None)
        if channel is None:
                raise ValueError(f"Channel with id {channel} not found.")
        return channel
