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
Class to interface with the voltage source Qblox S4g
"""
from dataclasses import dataclass
from time import sleep
from typing import Any

from qililab.config import logger
from qililab.instruments.current_source import CurrentSource
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings import QbloxS4g as QbloxS4gDriver
from qililab.typings.enums import Parameter


@InstrumentFactory.register
class QbloxS4g(CurrentSource):
    """Qblox S4g class

    Args:
        name (InstrumentName): name of the instrument
        device (Qblox_S4g): Instance of the qcodes S4g class.
        settings (QbloxS4gSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_S4G

    @dataclass
    class QbloxS4gSettings(CurrentSource.CurrentSourceSettings):
        """Contains the settings of a specific signal generator."""

    settings: QbloxS4gSettings
    device: QbloxS4gDriver

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
        channel.current(self.current[dac_index])
        logger.debug("SPI current set to %f", channel.current())
        while channel.is_ramping():
            sleep(0.1)

    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""

        if channel_id is None:
            if len(self.dacs) == 1:
                channel_id = self.dacs[0]
            else:
                raise ValueError(f"channel not specified to update instrument {self.name.value}")
        if channel_id > 3:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 4 -> maximum channel_id should be 3."
            )

        channel = self.dac(dac_index=channel_id) if self.is_device_active() else None

        if parameter == Parameter.CURRENT:
            self._set_current(value=value, channel_id=channel_id, channel=channel)
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
            if len(self.dacs) == 1:
                channel_id = self.dacs[0]
            else:
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
    def _set_current(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the current"""
        self.settings.current[channel_id] = float(value)

        if self.is_device_active():
            channel.current(self.current[channel_id])

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
        """Stop outputing current."""
        self.device.set_dacs_zero()
        for dac_index in self.settings.dacs:
            channel = self.dac(dac_index=dac_index)
            logger.debug("Dac%d current resetted to  %f", dac_index, channel.current())

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.device.set_dacs_zero()
