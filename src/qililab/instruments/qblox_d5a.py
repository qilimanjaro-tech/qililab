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

from typing import Callable

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument import InstrumentWithChannels
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.runcard.runcard_instruments import QbloxD5ARuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxD5AChannelSettings, QbloxD5ASettings
from qililab.typings import QbloxD5ADevice
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QBLOX_D5A)
class QbloxD5A(InstrumentWithChannels[QbloxD5ADevice, QbloxD5ASettings, QbloxD5AChannelSettings, int]):
    def __init__(self, settings: QbloxD5ASettings | None = None):
        super().__init__(settings=settings)

        for channel in self.settings.channels:
            self.add_channel_parameter(channel_id=channel.id, name="voltage", setting_key="voltage", get_driver_cmd=self._get_voltage, set_driver_cmd=self._set_voltage)
            self.add_channel_parameter(channel_id=channel.id, name="span", setting_key="span", get_driver_cmd=self._get_span, set_driver_cmd=self._set_span)
            self.add_channel_parameter(channel_id=channel.id, name="ramping_enabled", setting_key="ramping_enabled", get_driver_cmd=self._get_ramping_enabled, set_driver_cmd=self._set_ramping_enabled)
            self.add_channel_parameter(channel_id=channel.id, name="ramping_rate", setting_key="ramping_rate", get_driver_cmd=self._get_ramping_rate, set_driver_cmd=self._set_ramping_rate)

    @check_device_initialized
    def turn_on(self):
        raise NotImplementedError

    @check_device_initialized
    def turn_off(self):
        self.device.set_dacs_zero()

    @check_device_initialized
    def reset(self):
        self.device.set_dacs_zero()

    @check_device_initialized
    def initial_setup(self):
        for channel in self.settings.channels:
            self._set_span(channel.span, channel.id)
            self._set_ramping_rate(channel.ramping_rate, channel.id)
            self._set_ramping_enabled(channel.ramping_enabled, channel.id)
            self._set_voltage(channel.voltage, channel.id)

    @classmethod
    def get_default_settings(cls) -> QbloxD5ASettings:
        return QbloxD5ASettings(alias="d5a", channels=[QbloxD5AChannelSettings(id=id) for id in range(16)])

    def to_runcard(self) -> RuncardInstrument:
        return QbloxD5ARuncardInstrument(settings=self.settings)
    
    def _get_voltage(self, channel: int):
        getattr(self.device, f"dac{channel}").voltage()
    
    def _set_voltage(self, value: float, channel: int):
        getattr(self.device, f"dac{channel}").voltage(value)

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

    
