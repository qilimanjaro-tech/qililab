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

from qililab.types import TInstrument, TChannelID


class InstrumentParameter(Parameter, Generic[TInstrument, TChannelID]):
    def __init__(
        self,
        name: str,
        owner: TInstrument,
        setting_key: str,
        channel_id: Optional[TChannelID] = None,
        get_driver_cmd: Optional[Callable] = None,
        set_driver_cmd: Optional[Callable] = None,
        **kwargs
    ):
        """
        QCoDeS Parameter that integrates with the instrument's settings and device.

        Parameters:
            name: The name of the parameter.
            instrument: The instrument instance to which this parameter belongs.
            setting_key: The key in the settings model corresponding to this parameter.
            get_driver_cmd: Optional callable to retrieve the value from the driver.
            set_driver_cmd: Optional callable to set the value in the driver.
            **kwargs: Additional arguments for the QCoDeS `Parameter` class.
        """
        super().__init__(name=name, **kwargs)
        self.owner = owner
        self.setting_key = setting_key
        self.channel_id = channel_id
        self.get_driver_cmd = get_driver_cmd
        self.set_driver_cmd = set_driver_cmd

    def get_raw(self):
        # Prefer hardware call if get_driver_cmd is provided and the device is connected
        if self.get_driver_cmd and self.owner.is_device_active():
            value = self.get_driver_cmd()
            setattr(self.owner.settings, self.setting_key, value)
            return value
        
        # Retrieve value from channel settings if channel_id is specified
        if self.channel_id is not None:
            channel_settings = self.owner.settings.get_channel(self.channel_id)
            return getattr(channel_settings, self.setting_key)

        # Otherwise, retrieve from instrument-level settings
        return getattr(self.owner.settings, self.setting_key)

    def set_raw(self, value):
        # Update channel settings if channel_id is specified
        if self.channel_id is not None:
            channel_settings = self.owner.settings.get_channel(self.channel_id)
            setattr(channel_settings, self.setting_key, value)

            # Optionally call hardware-level update
            if self.set_driver_cmd and self.owner.is_device_active():
                self.set_driver_cmd(value, self.channel_id)

        # Update instrument-level settings if no channel is specified
        else:
            setattr(self.owner.settings, self.setting_key, value)

            # Optionally call hardware-level update
            if self.set_driver_cmd and self.owner.is_device_active():
                self.set_driver_cmd(value)
