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

"""QDevil QDAC-II Instrument"""

from dataclasses import dataclass

import numpy as np

from qililab.instruments import InstrumentFactory, ParameterNotFound, check_device_initialized, log_set_parameter
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue
from qililab.typings import QDevilQDac2 as QDevilQDac2Driver
from qililab.waveforms import Waveform


@InstrumentFactory.register
class QDevilQDac2(VoltageSource):
    """QDevil QDAC-II Intrument

    Args:
        name (InstrumentName): Name of the instrument
        device (QDevilQDac2): Instance of the QCoDes QDac2 class.
        settings (QDevilQDac2Settings): Settings of the instrument.
    """

    name = InstrumentName.QDEVIL_QDAC2

    @dataclass
    class QDevilQDac2Settings(VoltageSource.VoltageSourceSettings):
        """Contains the settings of a specific signal generator."""

        low_pass_filter: list[str]
        mode: str = "offset"

    settings: QDevilQDac2Settings
    device: QDevilQDac2Driver
    _cache: dict[int | str, bool] = {}  # noqa: RUF012

    @property
    def low_pass_filter(self):
        """QDAC-II `low_pass_filter` property.

        Returns:
            list[str]: A list of the low pass filter setting of each DACs.
        """
        return self.settings.low_pass_filter

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None):
        """Set parameter to the corresponding value for an instrument's channel.

        Args:
            parameter (Parameter): Name of the parameter to be updated
            value (float | str | bool): New value of the parameter
            channel_id (int | None): Channel identifier
        """
        self._validate_channel(channel_id=channel_id)

        channel = self.device.channel(channel_id) if self.is_device_active() else None

        index = self.dacs.index(channel_id)
        if parameter == Parameter.VOLTAGE:
            voltage = float(value)
            self.settings.voltage[index] = voltage
            if self.is_device_active():
                channel.dc_constant_V(voltage)
            return
        if parameter == Parameter.SPAN:
            span = str(value)
            self.settings.span[index] = span
            if self.is_device_active():
                channel.output_range(span)
            return
        if parameter == Parameter.RAMPING_ENABLED:
            ramping_enabled = bool(value)
            self.settings.ramping_enabled[index] = ramping_enabled
            if self.is_device_active():
                if ramping_enabled:
                    channel.dc_slew_rate_V_per_s(self.ramp_rate[index])
                else:
                    channel.dc_slew_rate_V_per_s(2e7)
            return
        if parameter == Parameter.RAMPING_RATE:
            ramping_rate = float(value)
            self.settings.ramp_rate[index] = ramping_rate
            ramping_enabled = self.ramping_enabled[index]
            if ramping_enabled and self.is_device_active():
                channel.dc_slew_rate_V_per_s(ramping_rate)
            return
        if parameter == Parameter.LOW_PASS_FILTER:
            low_pass_filter = str(value)
            self.settings.low_pass_filter[index] = low_pass_filter
            if self.is_device_active():
                channel.output_filter(low_pass_filter)
            return
        raise ParameterNotFound(self, parameter)

    def get_dac(self, channel_id: ChannelID):
        """Get specific DAC from QDAC.

        Args:
            channel_id (ChannelID): channel id of the dac
        """
        return self.device.channel(channel_id)

    def upload_waveform(self, waveform: Waveform, channel_id: ChannelID):
        """Uploads a waveform to the instrument and saves it to _cache.
        IMPORTANT: note that the waveform resolution is not to the ns, it is acutally around 1_micro_second.

        Args:
            waveform (Waveform): Waveform to upload
            channel_id (ChannelID): channel id of the qdac

        Raises:
            ValueError: if a waveform is already allocated
        """
        envelope = waveform.envelope()
        values = list(envelope)  # TODO: does np array work?
        if channel_id in self._cache:
            raise ValueError(
                f"Device {self.name} already has a waveform allocated to channel {channel_id}. Clear the cache before allocating a new waveform"
            )
        # check that waveform entries are multiple of 2, check that amplitudes are within [-1,1] range
        if len(envelope) % 2 != 0:
            raise ValueError("Waveform entries must be even.")
        if np.max(np.abs(envelope)) >= 1:
            raise ValueError("Waveform amplitudes must be within [-1,1] range.")
        trace = self.device.allocate_trace(channel_id, len(values))
        trace.waveform(values)
        self._cache[channel_id] = True

    def play(self, channel_id: ChannelID | None = None, clear_after: bool = True):
        """Plays a waveform for a given channel id. If no channel id is given, plays all waveforms stored in the cache.

        Args:
            channel_id (ChannelID | None, optional): Channel id to play a waveform through. Defaults to None.
            clear_after (bool): If True, clears cache. Defaults to True.
        """
        if channel_id is None:
            for dac in self.dacs:
                awg_context = self.get_dac(dac).arbitrary_wave(dac)
            self.device.start_all()
        else:
            awg_context = self.get_dac(channel_id).arbitrary_wave(channel_id)
            awg_context.start()
        if clear_after:
            self.clear_cache()

        # TODO: catch errors raised at self.device.errors()

    def clear_cache(self):
        """Clears the cache of the instrument"""
        self.device.remove_traces()  # TODO: this method should be run at initial setup if instrument is in awg mode
        self._cache = {}

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None):
        """Get parameter's value for an instrument's channel.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier.
        """
        self._validate_channel(channel_id=channel_id)

        index = self.dacs.index(channel_id)
        if hasattr(self.settings, parameter.value):
            return getattr(self.settings, parameter.value)[index]
        raise ParameterNotFound(self, parameter)

    @check_device_initialized
    def initial_setup(self):
        """Perform an initial setup."""
        for channel_id in self.dacs:
            self._validate_channel(channel_id=channel_id)

            index = self.dacs.index(channel_id)
            channel = self.device.channel(channel_id)
            channel.dc_mode("fixed")
            channel.output_range(self.span[index])
            channel.output_filter(self.low_pass_filter[index])
            if self.ramping_enabled[index]:
                channel.dc_slew_rate_V_per_s(self.ramp_rate[index])
            else:
                channel.dc_slew_rate_V_per_s(2e7)
            channel.dc_constant_V(0.0)

    @check_device_initialized
    def turn_on(self):
        """Start outputing voltage."""
        for channel_id in self.dacs:
            index = self.dacs.index(channel_id)
            channel = self.device.channel(channel_id)
            channel.dc_constant_V(self.voltage[index])

    @check_device_initialized
    def turn_off(self):
        """Stop outputing voltage."""
        for channel_id in self.dacs:
            channel = self.device.channel(channel_id)
            channel.dc_constant_V(0.0)

    @check_device_initialized
    def reset(self):
        """Reset instrument. This will affect all channels."""
        self.device.reset()

    def _validate_channel(self, channel_id: ChannelID | None):
        """Check if channel identifier is valid and in the allowed range."""
        if channel_id is None:
            raise ValueError(
                "QDevil QDAC-II is a multi-channel instrument. `channel_id` must be specified to get or set parameters."
            )

        channel_id = int(channel_id)
        if channel_id < 1 or channel_id > 24:
            raise ValueError(f"The specified `channel_id`: {channel_id} is out of range. Allowed range is [1, 24].")
