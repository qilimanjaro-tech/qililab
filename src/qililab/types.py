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

from typing import TYPE_CHECKING, Optional, TypeVar

if TYPE_CHECKING:
    from qililab.settings.instruments.channel_settings import ChannelSettings
    from qililab.settings.instruments.input_settings import InputSettings
    from qililab.settings.instruments.instrument_settings import InstrumentSettings
    from qililab.settings.instruments.output_settings import OutputSettings
    from qililab.typings.instruments import Device

TDevice = TypeVar("TDevice", bound="Device")
TInstrumentSettings = TypeVar("TInstrumentSettings", bound="InstrumentSettings")
TChannelSettings = TypeVar("TChannelSettings", bound=Optional["ChannelSettings"])
TChannelID = TypeVar("TChannelID", bound=Optional[int | str])
TOutputSettings = TypeVar("TOutputSettings", bound=Optional["OutputSettings"])
TInputSettings = TypeVar("TInputSettings", bound=Optional["InputSettings"])
