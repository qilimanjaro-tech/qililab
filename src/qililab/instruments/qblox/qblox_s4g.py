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
from __future__ import annotations

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument import InstrumentWithChannels
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.runcard.runcard_instruments import QbloxS4GRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxS4GChannelSettings, QbloxS4GSettings
from qililab.typings import QbloxS4GDevice


@InstrumentFactory.register(InstrumentType.QBLOX_S4G)
class QbloxS4G(InstrumentWithChannels[QbloxS4GDevice, QbloxS4GSettings, QbloxS4GChannelSettings, int]):
    def __init__(self, settings: QbloxS4GSettings | None = None):
        super().__init__(settings=settings)

        for channel in self.settings.channels:
            self.add_channel_parameter(channel_id=channel.id, name="current", settings_field="current", get_device_value=self._get_current, set_device_value=self._set_current)
            self.add_channel_parameter(channel_id=channel.id, name="span", settings_field="span", get_device_value=self._get_span, set_device_value=self._set_span)
            self.add_channel_parameter(channel_id=channel.id, name="ramping_enabled", settings_field="ramping_enabled", get_device_value=self._get_ramping_enabled, set_device_value=self._set_ramping_enabled)
            self.add_channel_parameter(channel_id=channel.id, name="ramping_rate", settings_field="ramping_rate", get_device_value=self._get_ramping_rate, set_device_value=self._set_ramping_rate)

    @classmethod
    def get_default_settings(cls) -> QbloxS4GSettings:
        return QbloxS4GSettings(alias="s4g", channels=[QbloxS4GChannelSettings(id=id) for id in range(4)])

    def to_runcard(self) -> RuncardInstrument:
        return QbloxS4GRuncardInstrument(settings=self.settings)

    @check_device_initialized
    def initial_setup(self):
        for channel in self.settings.channels:
            self._set_span(channel.span, channel.id)
            self._set_ramping_rate(channel.ramping_rate, channel.id)
            self._set_ramping_enabled(channel.ramping_enabled, channel.id)

    @check_device_initialized
    def turn_on(self):
        for channel in self.settings.channels:
            self._set_current(channel.curr, channel.id)

    @check_device_initialized
    def turn_off(self):
        for channel in self.settings.channels:
            self._set_current(0.0, channel.id)

    @check_device_initialized
    def reset(self):
        self.turn_off()
        for channel in self.settings.channels:
            self._set_current(channel.voltage, channel.id)

    def _get_current(self, channel: int):
        getattr(self.device, f"dac{channel}").current()

    def _set_current(self, value: float, channel: int):
        getattr(self.device, f"dac{channel}").current(value)

    def _get_span(self, channel: int):
        getattr(self.device, f"dac{channel}").span()

    def _set_span(self, value: str, channel: int):
        getattr(self.device, f"dac{channel}").span(value)

    def _get_ramping_enabled(self, channel: int):
        getattr(self.device, f"dac{channel}").ramping_enabled()

    def _set_ramping_enabled(self, value: bool, channel: int):
        getattr(self.device, f"dac{channel}").ramping_enabled(value)

    def _get_ramping_rate(self, channel: int):
        getattr(self.device, f"dac{channel}").ramp_rate()

    def _set_ramping_rate(self, value: float, channel: int):
        getattr(self.device, f"dac{channel}").ramp_rate(value)
