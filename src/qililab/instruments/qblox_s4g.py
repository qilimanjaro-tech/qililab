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
from qililab.runcard.runcard_instruments import QbloxS4GRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxS4GChannelSettings, QbloxS4GSettings
from qililab.typings import QbloxS4GDevice
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QBLOX_S4G)
class QbloxS4G(InstrumentWithChannels[QbloxS4GDevice, QbloxS4GSettings, QbloxS4GChannelSettings, int]):
    @check_device_initialized
    def turn_on(self):
        pass

    @check_device_initialized
    def turn_off(self):
        self.device.set_dacs_zero()

    @check_device_initialized
    def reset(self):
        self.device.set_dacs_zero()

    @check_device_initialized
    def initial_setup(self):
        for dac in self.settings.dacs:
            self._on_span_changed(dac.span, dac.id)
            self._on_ramping_rate_changed(dac.ramping_rate, dac.id)
            self._on_ramping_enabled_changed(dac.ramping_enabled, dac.id)
            self._on_current_changed(dac.current, dac.id)

    @classmethod
    def get_default_settings(cls) -> QbloxS4GSettings:
        return QbloxS4GSettings(alias="s4g", channels=[QbloxS4GChannelSettings(id=id) for id in range(4)])

    def _on_current_changed(self, value: float, channel: int):
        getattr(self.device, f"dac{channel}").current(value)

    def _on_span_changed(self, value: str, channel: int):
        getattr(self.device, f"dac{channel}").span(value)

    def _on_ramping_enabled_changed(self, value: bool, channel: int):
        getattr(self.device, f"dac{channel}").ramping_enabled(value)

    def _on_ramping_rate_changed(self, value: float, channel: int):
        getattr(self.device, f"dac{channel}").ramp_rate(value)

    def to_runcard(self) -> RuncardInstrument:
        return QbloxS4GRuncardInstrument(settings=self.settings)
