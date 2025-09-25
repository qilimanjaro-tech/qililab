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

"""
Class to interface with the voltage source Qblox D5a
"""

from dataclasses import dataclass
from time import sleep
from typing import Any

from qililab.config import logger
from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import ChannelID, InstrumentName, OutputID, Parameter, ParameterValue
from qililab.typings import QbloxD5a as QbloxD5aDriver


@InstrumentFactory.register
class QbloxD5a(VoltageSource):
    """Qblox D5a class

    Args:
        name (InstrumentName): name of the instrument
        device (Qblox_D5a): Instance of the qcodes D5a class.
        settings (QbloxD5aSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_D5A

    @dataclass
    class QbloxD5aSettings(VoltageSource.VoltageSourceSettings):
        """Contains the settings of a specific signal generator."""

    settings: QbloxD5aSettings
    device: QbloxD5aDriver

    def dac(self, dac_index: int):
        """get channel associated to the specific dac

        Args:
            dac_index (int): channel index

        Returns:
            _type_: _description_
        """
        return getattr(self.device, f"dac{dac_index}")

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None, output_id: OutputID | None = None):
        """Set Qblox instrument calibration settings."""

        if channel_id is None:
            raise ValueError(f"channel not specified to update instrument {self.name.value}")

        channel_id = int(channel_id)
        if channel_id > 15:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 16 -> maximum channel_id should be 15."
            )

        channel = self.dac(dac_index=channel_id) if self.is_device_active() else None

        if parameter == Parameter.VOLTAGE:
            self._set_voltage(value=value, channel_id=channel_id, channel=channel)
            return
        if parameter == Parameter.SPAN:
            self._set_span(value=value, channel_id=channel_id, channel=channel)
            return
        if parameter == Parameter.RAMPING_ENABLED:
            self._set_ramping_enabled(value=value, channel_id=channel_id, channel=channel)
            return
        if parameter == Parameter.RAMPING_RATE:
            self._set_ramping_rate(value=value, channel_id=channel_id, channel=channel)
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None, output_id: OutputID | None = None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier of the parameter to update.
        """
        if channel_id is None:
            raise ValueError(f"channel not specified to update instrument {self.name.value}")

        channel_id = int(channel_id)
        if channel_id > 15:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 16 -> maximum channel_id should be 15."
            )
        if hasattr(self.settings, parameter.value):
            return getattr(self.settings, parameter.value)[channel_id]
        raise ParameterNotFound(self, parameter)

    def _set_voltage(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the voltage"""
        self.settings.voltage[channel_id] = float(value)
        if self.is_device_active():
            channel.voltage(self.voltage[channel_id])

    def _set_span(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the span"""
        self.settings.span[channel_id] = str(value)
        if self.is_device_active():
            channel.span(self.span[channel_id])

    def _set_ramping_enabled(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the ramping_enabled"""
        self.settings.ramping_enabled[channel_id] = bool(value)
        if self.is_device_active():
            channel.ramping_enabled(self.ramping_enabled[channel_id])

    def _set_ramping_rate(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the ramp_rate"""
        self.settings.ramp_rate[channel_id] = float(value)
        if self.is_device_active():
            channel.ramp_rate(self.ramp_rate[channel_id])

    @check_device_initialized
    def initial_setup(self):
        """performs an initial setup."""
        for channel_id in self.dacs:
            index = self.dacs.index(channel_id)
            channel = self.dac(dac_index=channel_id)
            channel.ramping_enabled(self.ramping_enabled[index])
            channel.ramp_rate(self.ramp_rate[index])
            channel.span(self.span[index])
            channel.voltage(self.voltage[index])
            logger.debug("SPI voltage set to %f", channel.voltage())
            while channel.is_ramping():
                sleep(0.1)

    @check_device_initialized
    def turn_on(self):
        """Dummy method."""

    @check_device_initialized
    def turn_off(self):
        """Stop outputing voltage."""
        for dac_index in self.settings.dacs:
            channel = self.dac(dac_index=dac_index)
            channel.voltage(0)
            logger.debug("Dac%d voltage resetted to  %f", dac_index, channel.voltage())

    @check_device_initialized
    def reset(self):
        """Reset instrument."""
        for dac_index in self.settings.dacs:
            channel = self.dac(dac_index=dac_index)
            channel.voltage(0)
