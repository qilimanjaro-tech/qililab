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

from typing import TYPE_CHECKING, Callable, ClassVar

import numpy as np

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument import InstrumentWithChannels
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.runcard.runcard_instruments import QDevilQDAC2RuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QDevilQDAC2ChannelSettings, QDevilQDAC2Settings
from qililab.typings import QDevilQDAC2Device as QDevilQDac2Driver
from qililab.typings.enums import Parameter

if TYPE_CHECKING:
    from qililab.waveforms import Waveform


@InstrumentFactory.register(InstrumentType.QDEVIL_QDAC2)
class QDevilQDAC2(InstrumentWithChannels[QDevilQDac2Driver, QDevilQDAC2Settings, QDevilQDAC2ChannelSettings, int]):
    AWG_RESOLUTION: ClassVar[int] = 1000

    def __init__(self, settings: QDevilQDAC2Settings | None = None):
        super().__init__(settings=settings)
        for channel in self.settings.channels:
            self.add_channel_parameter(
                channel_id=channel.id,
                name="voltage",
                settings_field="voltage",
                get_device_value=self._get_voltage,
                set_device_value=self._set_voltage,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="span",
                settings_field="span",
                get_device_value=self._get_span,
                set_device_value=self._set_span,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="ramping_enabled",
                settings_field="ramping_enabled",
                set_device_value=self._set_ramping_enabled,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="ramping_rate",
                settings_field="ramping_rate",
                get_device_value=self._get_ramping_rate,
                set_device_value=self._set_ramping_rate,
            )

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
        return QDevilQDAC2Settings(alias="qdac2", channels=[QDevilQDAC2ChannelSettings(id=index) for index in range(24)])

    def _get_voltage(self, channel: int):
        self.device.channel(channel).dc_constant_V()

    def _set_voltage(self, value: float, channel: int):
        self.device.channel(channel).dc_constant_V(value)

    def _get_span(self, channel: int):
        self.device.channel(channel).output_range()

    def _set_span(self, value: str, channel: int):
        self.device.channel(channel).output_range(value)

    def _set_ramping_enabled(self, value: bool, channel: int):
        if value:
            ramping_rate = self.settings.get_channel(channel).ramping_rate
            self.device.channel(channel).dc_slew_rate_V_per_s(ramping_rate)
        else:
            self.device.channel(channel).dc_slew_rate_V_per_s(2e7)

    def _get_ramping_rate(self, channel: int):
        return self.device.channel(channel).dc_slew_rate_V_per_s()

    def _set_ramping_rate(self, value: float, channel: int):
        ramping_enabled = self.settings.get_channel(channel).ramping_enabled
        if ramping_enabled:
            self.device.channel(channel).dc_slew_rate_V_per_s(value)

    def _set_low_pas_filter(self, value: str, channel: int):
        self.device.channel(channel).output_filter(value)

    def to_runcard(self) -> RuncardInstrument:
        return QDevilQDAC2RuncardInstrument(settings=self.settings)

    def upload_waveform(self, waveform: Waveform, channel: int):
        """Uploads a waveform to the instrument and saves it to _cache.
        IMPORTANT: note that the waveform resolution is not to the ns, it is acutally around 1_micro_second.

        Args:
            waveform (Waveform): Waveform to upload
            channel_id (ChannelID): channel id of the qdac

        Raises:
            ValueError: if a waveform is already allocated
        """
        envelope = waveform.envelope(self.AWG_RESOLUTION)
        if channel in self._cache:
            raise ValueError(
                f"QDAC2 {self.alias} already has a waveform allocated to channel {channel}. Clear the cache before allocating a new waveform."
            )
        # check that waveform entries are multiple of 2, check that amplitudes are within [-1,1] range
        if len(envelope) % 2 != 0:
            raise ValueError("Waveform entries must be even.")
        if np.max(np.abs(envelope)) >= 1:
            raise ValueError("Waveform amplitudes must be within [-1,1] range.")
        trace = self.device.allocate_trace(channel, len(envelope))
        trace.waveform(envelope)
        self._cache[channel] = True

    def play(self, channel: int | None = None, clear_after: bool = True):
        """Plays a waveform for a given channel id. If no channel id is given, plays all waveforms stored in the cache.

        Args:
            channel_id (ChannelID | None, optional): Channel id to play a waveform through. Defaults to None.
            clear_after (bool): If True, clears cache. Defaults to True.
        """
        if channel is None:
            for dac in self.settings.channels:
                awg_context = self.device.channel(dac.id).arbitrary_wave(dac.id)
            self.device.start_all()
        else:
            awg_context = self.device.channel(channel).arbitrary_wave(channel)
            awg_context.start()
        if clear_after:
            self.clear_cache()

        # TODO: catch errors raised at self.device.errors()

    def clear_cache(self):
        """Clears the cache of the instrument"""
        self.device.remove_traces()  # TODO: this method should be run at initial setup if instrument is in awg mode
        self._cache = {}
