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
from pickle import NONE

import numpy as np
from qcodes_contrib_drivers.drivers.QDevil.QDAC2 import List_Context, QDac2Trigger_Context

from qililab.instruments import InstrumentFactory, ParameterNotFound, check_device_initialized, log_set_parameter
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue
from qililab.typings import QDevilQDac2 as QDevilQDac2Driver
from qililab.waveforms import Waveform
from qililab.waveforms.arbitrary import Arbitrary


@InstrumentFactory.register
class QDevilQDac2(VoltageSource):
    """QDevil QDAC-II Intrument

    Args:
        name (InstrumentName): Name of the instrument
        device (QDevilQDac2): Instance of the QCoDes QDac2 class.
        settings (QDevilQDac2Settings): Settings of the instrument.
    """

    _MIN_RAMPING_RATE: float = 0.01
    _MAX_RAMPING_RATE: float = 2e7
    name = InstrumentName.QDEVIL_QDAC2

    @dataclass
    class QDevilQDac2Settings(VoltageSource.VoltageSourceSettings):
        """Contains the settings of a specific signal generator."""

        low_pass_filter: list[str]
        mode: str = "offset"

    settings: QDevilQDac2Settings
    device: QDevilQDac2Driver
    _cache_aws: dict[int | str, bool] = {}  # noqa: RUF012
    _cache_dc: dict[int | str, List_Context] = {}  # noqa: RUF012
    _triggers: dict[str, QDac2Trigger_Context] = {}  # noqa: RUF012

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
                channel.dc_constant_V(voltage)  # type: ignore[union-attr]
            return
        if parameter == Parameter.SPAN:
            span = str(value)
            self.settings.span[index] = span
            if self.is_device_active():
                channel.output_range(span)  # type: ignore[union-attr]
            return
        if parameter == Parameter.RAMPING_ENABLED:
            ramping_enabled = bool(value)
            self.settings.ramping_enabled[index] = ramping_enabled
            if self.is_device_active():
                if ramping_enabled:
                    if (
                        self.ramp_rate[index] < QDevilQDac2._MIN_RAMPING_RATE
                        or self.ramp_rate[index] > QDevilQDac2._MAX_RAMPING_RATE
                    ):
                        raise ValueError(
                            f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
                        )
                    channel.dc_slew_rate_V_per_s(self.ramp_rate[index])  # type: ignore[union-attr]
                else:
                    channel.dc_slew_rate_V_per_s(2e7)  # type: ignore[union-attr]
            return
        if parameter == Parameter.RAMPING_RATE:
            ramping_rate = float(value)
            self.settings.ramp_rate[index] = ramping_rate
            ramping_enabled = self.ramping_enabled[index]
            if ramping_enabled and self.is_device_active():
                if ramping_rate < QDevilQDac2._MIN_RAMPING_RATE or ramping_rate > QDevilQDac2._MAX_RAMPING_RATE:
                    raise ValueError(
                        f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
                    )
                channel.dc_slew_rate_V_per_s(ramping_rate)  # type: ignore[union-attr]
            return
        if parameter == Parameter.LOW_PASS_FILTER:
            low_pass_filter = str(value)
            self.settings.low_pass_filter[index] = low_pass_filter
            if self.is_device_active():
                channel.output_filter(low_pass_filter)  # type: ignore[union-attr]
            return
        raise ParameterNotFound(self, parameter)

    def get_dac(self, channel_id: ChannelID):
        """Get specific DAC from QDAC.

        Args:
            channel_id (ChannelID): channel id of the dac
        """
        return self.device.channel(channel_id)

    def upload_awg_waveform(self, waveform: Waveform, channel_id: ChannelID):
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
        if channel_id in self._cache_aws:
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
        self._cache_aws[channel_id] = True

    def play_awg(self, channel_id: ChannelID | None = None, clear_after: bool = True):
        """Plays a waveform for a given channel id. If no channel id is given, plays all waveforms stored in the cache.

        Args:
            channel_id (ChannelID, optional): Channel id to play a waveform through. Defaults to None.
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

    def upload_trigger_pulse(
        self,
        channel_id: ChannelID,
        ramp_up_us: int,
        ramp_down_us: int,
        dwell_us: int,
        pulse_duration_us: int,
        pulse_v: float,
        in_port: int,
        out_port: int | None = None,
        offset_v: float | None = None,
        delay_s: float = 0,
        trigger_width: float = 1e-6,
    ):
        """Create a triggered pulse that sends another trigger at the end of the pulse.
        For communication with another machine

        Args:
            channel_id (ChannelID): Channel identifier.
            in_port (int): input trigger port.
            out_port (int): output trigger port
            ramp_up_us (int): _description_
            ramp_down_us (int): _description_
            dwell_us (int): _description_
            pulse_duration_us (int): _description_
            pulse_v (float): _description_
            offset_v (float | None, optional): _description_. Defaults to None.
            delay_s (float, optional): _description_. Defaults to 0.
            trigger_width (float, optional): _description_. Defaults to 1e-6.
        """
        # Create the pulse sequence and upload as a dc list
        if not offset_v:
            offset_v = float(self.device.channel(channel_id).dc_constant_V())
        offset_ramp_up = np.linspace(offset_v, pulse_v, int(ramp_up_us / dwell_us))
        offset_ramp_down = np.linspace(pulse_v, offset_v, int(ramp_down_us / dwell_us))
        offset_pulse = np.ones(int(pulse_duration_us / dwell_us)) * pulse_v
        volt_pulse = np.concatenate([offset_ramp_up, offset_pulse, offset_ramp_down])
        volt_waveform = Arbitrary(samples=volt_pulse)

        self.upload_voltage_list(volt_waveform, channel_id, dwell_us, delay_s)

        # Set triggers received to start (in) and sent at the end (out)
        self.set_in_external_trigger(channel_id, in_port)
        if out_port:
            self.set_out_external_trigger(channel_id, out_port, f"ext_{out_port}_ch_{channel_id}", trigger_width)

    def upload_voltage_list(self, waveform: Waveform, channel_id: ChannelID, dwell_us: int = 1, delay_s: float = 0):

        if channel_id in self._cache_dc:
            raise ValueError(
                f"Device {self.name} already has a waveform allocated to channel {channel_id}. Clear the cache before allocating a new waveform"
            )

        envelope = waveform.envelope()
        channel = self.device.channel(channel_id)

        dc_list = channel.dc_list(voltages=list(envelope), dwell_s=dwell_us * 10e-6, delay_s=delay_s)
        self._cache_dc[channel_id] = dc_list

    def set_in_external_trigger(self, channel_id: ChannelID, in_port: int):
        if not channel_id in self._cache_dc.keys():
            raise ValueError(
                f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}"
            )
        self._cache_dc[channel_id].start_on_external(in_port)

    def set_out_external_trigger(self, channel_id: ChannelID, out_port: int, trigger: str, width_s: float = 1e-6):
        if not channel_id in self._cache_dc.keys():
            raise ValueError(
                f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}"
            )
        if not str(trigger) in self._triggers.keys():
            self._triggers[str(trigger)] = self._cache_dc[channel_id].end_marker()
        self.device.connect_external_trigger(port=out_port, trigger=self._triggers[str(trigger)], width_s=width_s)

    def clear_cache(self):
        """Clears the cache of the instrument"""
        self.device.remove_traces()  # TODO: this method should be run at initial setup if instrument is in awg mode
        self._cache_aws = {}
        self._cache_dc = {}

    def clear_trigger(self, trigger: str | None = None):
        if trigger:
            self.device.free_trigger(str(trigger))
        self.device.free_all_triggers()

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
                if (
                    self.ramp_rate[index] < QDevilQDac2._MIN_RAMPING_RATE
                    or self.ramp_rate[index] > QDevilQDac2._MAX_RAMPING_RATE
                ):
                    raise ValueError(
                        f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
                    )
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
        if self._trigger:
            self._trigger.close()

    @check_device_initialized
    def reset(self):
        """Reset instrument. This will affect all channels."""
        if self._trigger:
            self._trigger.close()
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
