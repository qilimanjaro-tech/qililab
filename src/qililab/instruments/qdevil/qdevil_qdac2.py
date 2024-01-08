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

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import InstrumentName
from qililab.typings import QDevilQDac2 as QDevilQDac2Driver
from qililab.typings.enums import Parameter


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

    settings: QDevilQDac2Settings
    device: QDevilQDac2Driver

    @property
    def low_pass_filter(self):
        """QDAC-II `low_pass_filter` property.

        Returns:
            list[str]: A list of the low pass filter setting of each DACs.
        """
        return self.settings.low_pass_filter

    def setup(  # pylint: disable=too-many-branches
        self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None
    ):
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
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    def get(self, parameter: Parameter, channel_id: int | None = None):
        """Get parameter's value for an instrument's channel.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier.
        """
        self._validate_channel(channel_id=channel_id)

        index = self.dacs.index(channel_id)
        if hasattr(self.settings, parameter.value):
            return getattr(self.settings, parameter.value)[index]
        raise ParameterNotFound(f"Could not find parameter {parameter} in instrument {self.name}")

    @Instrument.CheckDeviceInitialized
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

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Start outputing voltage."""
        for channel_id in self.dacs:
            index = self.dacs.index(channel_id)
            channel = self.device.channel(channel_id)
            channel.dc_constant_V(self.voltage[index])

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop outputing voltage."""
        for channel_id in self.dacs:
            channel = self.device.channel(channel_id)
            channel.dc_constant_V(0.0)

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument. This will affect all channels."""
        self.device.reset()

    def _validate_channel(self, channel_id: int | None):
        """Check if channel identifier is valid and in the allowed range."""
        if channel_id is None:
            raise ValueError(
                "QDevil QDAC-II is a multi-channel instrument. `channel_id` must be specified to get or set parameters."
            )
        if channel_id < 1 or channel_id > 24:
            raise ValueError(f"The specified `channel_id`: {channel_id} is out of range. Allowed range is [1, 24].")
