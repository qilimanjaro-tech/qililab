# Copyright 2025 Qilimanjaro Quantum Tech
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

from dataclasses import dataclass
from typing import cast

from qililab.constants import DEFAULT_TIMEOUT
from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings.instruments.rswu_sp16tr import BeckerRSWUSP16TR

_CHANNELS = tuple(f"RF{i}" for i in range(1, 17))


@InstrumentFactory.register
class RSWUSP16TR(Instrument):
    """Becker Nachrichtentechnik RSWU-SP16TR RF switch."""

    # Update this enum key to whatever you use in your codebase (e.g. InstrumentName.RSWU_SP16TR)
    name = InstrumentName.RSWU_SP16TR
    timeout: int = DEFAULT_TIMEOUT

    @dataclass
    class RSWUSP16TRSettings(Instrument.InstrumentSettings):
        """Settings for the RF switch."""
        active_channel: str | None = None

    settings: RSWUSP16TRSettings
    device: BeckerRSWUSP16TR

    @property
    def active_channel(self) -> str | None:
        """Currently routed output channel.

        Returns:
            str: settings.active_channel.
        """
        return self.settings.active_channel

    @log_set_parameter
    def route(self, channel: str):
        """Route to a specific output

        Args:
            channel (str): name of the channel, valid: RF1..RF16.
        """
        if channel not in _CHANNELS:
            raise ValueError(f"Invalid channel '{channel}'. Expected one of {list(_CHANNELS)}.")
        self.settings.active_channel = channel
        if self.is_device_active():
            self.device.active_channel(channel)

    def query_active(self) -> str:
        """Query active channel from the device and update settings.

        Returns:
            str: settings.active_channel.
        """
        ch = self.device.active_channel.get()
        self.settings.active_channel = cast("str", ch)

        return ch

    def initial_setup(self):
        """Apply settings to the hardware."""
        if self.settings.active_channel is not None:
            self.device.active_channel(self.settings.active_channel)

    def update_settings(self):
        """Pull device state into settings."""
        self.settings.active_channel = self.device.active_channel.get()

    def to_dict(self):
        """Return a dict representation.

        Returns:
            dict.
        """
        return dict(super().to_dict().items())

    def set_parameter(self, parameter, value, channel_id=None):
        """Set instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            value (ParameterValue): value to update the Parameter with
            channel_id (int): Channel identifier of the parameter to update.
        """
        if parameter == "active_channel":
            self.route(str(value))
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(self, parameter, channel_id=None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): channel id of the parameter to get.

        Returns:
            ParameterValue.
        """
        if parameter == "active_channel":
            # ensure it's in sync
            self.settings.active_channel = self.device.active_channel.get()
            return cast("str", self.settings.active_channel)

        raise ParameterNotFound(self, parameter)

    @check_device_initialized
    def turn_on(self):
        """Turn on an instrument."""

    @check_device_initialized
    def turn_off(self):
        """Turn off an instrument."""

    @check_device_initialized
    def reset(self):
        """The wrapper doesn't allow a reset for this instrument"""
