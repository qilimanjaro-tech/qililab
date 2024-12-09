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
from typing import Callable, Generic, Optional

from qcodes import Parameter

from qililab.config import logger
from qililab.types import TChannelID, TInstrument


class InstrumentParameter(Parameter, Generic[TInstrument, TChannelID]):
    def __init__(
        self,
        name: str,
        owner: TInstrument,
        settings_field: str,
        channel_id: Optional[TChannelID] = None,
        get_device_value: Optional[Callable] = None,
        set_device_value: Optional[Callable] = None,
        **kwargs
    ):
        """
        QCoDeS Parameter that integrates with the instrument's settings and device.

        Parameters:
            name: The name of the parameter.
            instrument: The instrument instance to which this parameter belongs to.
            settings_field: The field name in the settings model corresponding to this parameter.
            get_device_value: Optional callable to retrieve the value from the device.
            set_device_value: Optional callable to set the value in the device.
            **kwargs: Additional arguments for the QCoDeS `Parameter` class.
        """
        super().__init__(name=name, **kwargs)
        self.owner = owner
        self.settings_field = settings_field
        self.channel_id = channel_id
        self.get_device_value = get_device_value
        self.set_device_value = set_device_value

    def get_raw(self):
        # Determine settings source
        settings_source = (
            self.owner.settings.get_channel(self.channel_id)
            if self.channel_id is not None
            else self.owner.settings
        )
        settings_value = getattr(settings_source, self.settings_field)

        # Check for hardware consistency if device is active and can provide the value
        if self.owner.is_device_active() and self.get_device_value:
            device_value = (
                self.get_device_value(self.channel_id)
                if self.channel_id is not None
                else self.get_device_value()
            )
            if device_value != settings_value:
                setattr(settings_source, self.settings_field, device_value)
                logger.warning(
                    "Parameter %s for instrument %s%s has inconsistent value between "
                    "device and settings. Updated settings with value retrieved from device.",
                    self.name,
                    self.owner.alias,
                    f" and channel {self.channel_id}" if self.channel_id is not None else "",
                )
            return device_value

        # Return settings value as fallback
        return settings_value

    def set_raw(self, value):
        # Determine settings source
        settings_source = (
            self.owner.settings.get_channel(self.channel_id)
            if self.channel_id is not None
            else self.owner.settings
        )
        setattr(settings_source, self.settings_field, value)

        # Call hardware-level update if applicable
        if self.owner.is_device_active() and self.set_device_value:
            self.set_device_value(value, *(self.channel_id,) if self.channel_id is not None else ())

    def __repr__(self):
        """
        Custom representation for InstrumentParameter.
        Includes name, channel ID (if applicable), and current value.
        """
        current_value = self.get()

        if self.channel_id is not None:
            return (
                f"InstrumentParameter(name={self.name}, "
                f"channel_id={self.channel_id}, value={current_value})"
            )
        return (
            f"InstrumentParameter(name={self.name}, "
            f"value={current_value})"
        )
