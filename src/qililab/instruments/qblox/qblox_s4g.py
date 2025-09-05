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
from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import ChannelID, InstrumentName, OutputID, Parameter, ParameterValue
from qililab.typings import QbloxS4g as QbloxS4gDriver


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

    @log_set_parameter
    def set_parameter(
        self,
        parameter: Parameter,
        value: ParameterValue,
        channel_id: ChannelID | None = None,
        output_id: OutputID | None = None,
    ):
        """Set Qblox instrument calibration settings."""

        if channel_id is None:
            if len(self.dacs) == 1:
                channel_id = self.dacs[0]
            else:
                raise ValueError(f"channel not specified to update instrument {self.name.value}")

        channel_id = int(channel_id)
        if channel_id > 3:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 4 -> maximum channel_id should be 3."
            )

        channel = self.dac(dac_index=channel_id) if self.is_device_active() else None

        if parameter == Parameter.CURRENT:
            self._set_current(value=float(value), channel_id=channel_id, channel=channel)
            return
        if parameter == Parameter.SPAN:
            self._set_span(value=float(value), channel_id=channel_id, channel=channel)
            return
        if parameter == Parameter.RAMPING_ENABLED:
            self._set_ramping_enabled(value=bool(value), channel_id=channel_id, channel=channel)
            return
        if parameter == Parameter.RAMPING_RATE:
            self._set_ramping_rate(value=float(value), channel_id=channel_id, channel=channel)
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(
        self, parameter: Parameter, channel_id: ChannelID | None = None, output_id: OutputID | None = None
    ):
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

        channel_id = int(channel_id)
        if channel_id > 3:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 4 -> maximum channel_id should be 3."
            )
        if hasattr(self.settings, parameter.value):
            index = self.dacs.index(channel_id)
            return getattr(self.settings, parameter.value)[index]
        raise ParameterNotFound(self, parameter)

    def _set_current(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the current"""
        index = self.dacs.index(channel_id)
        self.settings.current[index] = float(value)

        if self.is_device_active():
            channel.current(self.current[index])

    def _set_span(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the span"""
        index = self.dacs.index(channel_id)
        self.settings.span[index] = str(value)

        if self.is_device_active():
            channel.span(self.span[index])

    def _set_ramping_enabled(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the ramping_enabled"""
        index = self.dacs.index(channel_id)
        self.settings.ramping_enabled[index] = bool(value)

        if self.is_device_active():
            channel.ramping_enabled(self.ramping_enabled[index])

    def _set_ramping_rate(self, value: float | str | bool, channel_id: int, channel: Any):
        """Set the ramp_rate"""
        index = self.dacs.index(channel_id)
        self.settings.ramp_rate[index] = float(value)

        if self.is_device_active():
            channel.ramp_rate(self.ramp_rate[index])

    @check_device_initialized
    def initial_setup(self):
        """performs an initial setup."""
        for channel_id in self.dacs:
            index = self.dacs.index(channel_id)
            channel = self.dac(dac_index=channel_id)
            channel.ramping_enabled(self.ramping_enabled[index])
            channel.ramp_rate(self.ramp_rate[index])
            channel.span(self.span[index])
            channel.current(self.current[index])
            logger.debug("SPI current set to %f", channel.current())
            while channel.is_ramping():
                sleep(0.1)

    @check_device_initialized
    def turn_on(self):
        """Dummy method."""

    @check_device_initialized
    def turn_off(self):
        """Stop outputing current."""
        for channel_id in self.settings.dacs:
            channel = self.dac(dac_index=channel_id)
            channel.current(0)

    @check_device_initialized
    def reset(self):
        """Reset instrument."""
        for channel_id in self.settings.dacs:
            channel = self.dac(dac_index=channel_id)
            channel.current(0)
