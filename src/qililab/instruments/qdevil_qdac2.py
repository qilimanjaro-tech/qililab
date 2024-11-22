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

from typing import Callable

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument2 import Instrument2
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.runcard.runcard_instruments import QDevilQDAC2RuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QDevilQDAC2ChannelSettings, QDevilQDAC2Settings
from qililab.typings import QDevilQDAC2Device as QDevilQDac2Driver
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QDEVIL_QDAC2)
class QDevilQDAC2(Instrument2[QDevilQDac2Driver, QDevilQDAC2Settings, QDevilQDAC2ChannelSettings, int]):
    @check_device_initialized
    def turn_on(self):
        raise NotImplementedError

    @check_device_initialized
    def turn_off(self):
        raise NotImplementedError

    @check_device_initialized
    def reset(self):
        raise NotImplementedError

    @check_device_initialized
    def initial_setup(self):
        raise NotImplementedError

    @classmethod
    def get_default_settings(cls) -> QDevilQDAC2Settings:
        return QDevilQDAC2Settings(alias="qdac2", dacs=[QDevilQDAC2ChannelSettings(id=index) for index in range(24)])

    @classmethod
    def parameter_to_instrument_settings(cls) -> dict[Parameter, str]:
        return {}

    @classmethod
    def parameter_to_channel_settings(cls) -> dict[Parameter, str]:
        return {
            Parameter.VOLTAGE: "voltage",
            Parameter.SPAN: "span",
            Parameter.RAMPING_ENABLED: "ramping_enabled",
            Parameter.RAMPING_RATE: "ramping_rate",
            Parameter.LOW_PASS_FILTER: "low_pass_filter",
        }

    def get_channel_settings(self, channel: int) -> QDevilQDAC2ChannelSettings:
        for channel_settings in self.settings.dacs:
            if channel_settings.id == channel:
                return channel_settings
        raise ValueError(f"Channel {channel} not found.")

    def parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return {
            Parameter.VOLTAGE: self._on_voltage_changed,
            Parameter.SPAN: self._on_span_changed,
            Parameter.RAMPING_ENABLED: self._on_ramping_enabled_changed,
            Parameter.RAMPING_RATE: self._on_ramping_rate_changed,
            Parameter.LOW_PASS_FILTER: self._on_low_pas_filter_changed,
        }

    def _on_voltage_changed(self, value: float, channel: int):
        self.device.channel(channel).dc_constant_V(value)

    def _on_span_changed(self, value: str, channel: int):
        self.device.channel(channel).output_range(value)

    def _on_ramping_enabled_changed(self, value: bool, channel: int):
        if value:
            ramping_rate = self.get_channel_settings(channel).ramping_rate
            self.device.channel(channel).dc_slew_rate_V_per_s(ramping_rate)
        else:
            self.device.channel(channel).dc_slew_rate_V_per_s(2e7)

    def _on_ramping_rate_changed(self, value: float, channel: int):
        ramping_enabled = self.get_channel_settings(channel).ramping_enabled
        if ramping_enabled:
            self.device.channel(channel).dc_slew_rate_V_per_s(value)

    def _on_low_pas_filter_changed(self, value: str, channel: int):
        self.device.channel(channel).output_filter(value)

    def to_runcard(self) -> RuncardInstrument:
        return QDevilQDAC2RuncardInstrument(settings=self.settings)
