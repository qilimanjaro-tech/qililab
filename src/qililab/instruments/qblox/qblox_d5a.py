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
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import InstrumentName
from qililab.typings import QbloxD5a as QbloxD5aDriver
from qililab.typings.enums import Parameter


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

    def _channel_setup(self, dac_index: int) -> None:
        """Setup for a specific dac channel

        Args:
            dac_index (int): dac specific index channel
        """
        channel = self.dac(dac_index=dac_index)
        channel.ramping_enabled(self.ramping_enabled[dac_index])
        channel.ramp_rate(self.ramp_rate[dac_index])
        channel.span(self.span[dac_index])
        channel.voltage(self.voltage[dac_index])
        logger.debug("SPI voltage set to %f", channel.voltage())
        while channel.is_ramping():
            sleep(0.1)

    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""

        if channel_id is None:
            raise ValueError(f"channel not specified to update instrument {self.name.value}")
        if channel_id > 3:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 4 -> maximum channel_id should be 3."
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
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    def get(self, parameter: Parameter, channel_id: int | None = None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier of the parameter to update.
        """
        if channel_id is None:
            raise ValueError(f"channel not specified to update instrument {self.name.value}")
        if channel_id > 3:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 4 -> maximum channel_id should be 3."
            )
        if hasattr(self.settings, parameter.value):
            return getattr(self.settings, parameter.value)[channel_id]
        raise ParameterNotFound(f"Could not find parameter {parameter} in instrument {self.name}")

    @Instrument.CheckParameterValueFloatOrInt
    def _set_voltage(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the voltage"""
        self.settings.voltage[channel_id] = float(value)
        if self.is_device_active():
            channel.voltage(self.voltage[channel_id])

    @Instrument.CheckParameterValueString
    def _set_span(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the span"""
        self.settings.span[channel_id] = str(value)
        if self.is_device_active():
            channel.span(self.span[channel_id])

    @Instrument.CheckParameterValueBool
    def _set_ramping_enabled(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the ramping_enabled"""
        self.settings.ramping_enabled[channel_id] = bool(value)
        if self.is_device_active():
            channel.ramping_enabled(self.ramping_enabled[channel_id])

    @Instrument.CheckParameterValueFloatOrInt
    def _set_ramping_rate(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the ramp_rate"""
        self.settings.ramp_rate[channel_id] = float(value)
        if self.is_device_active():
            channel.ramp_rate(self.ramp_rate[channel_id])

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        for dac_index in self.dacs:
            self._channel_setup(dac_index=dac_index)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Dummy method."""

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop outputing voltage."""
        self.device.set_dacs_zero()
        for dac_index in self.settings.dacs:
            channel = self.dac(dac_index=dac_index)
            logger.debug("Dac%d voltage resetted to  %f", dac_index, channel.voltage())

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.device.set_dacs_zero()
