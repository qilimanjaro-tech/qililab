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

"""GS200 class"""
from dataclasses import dataclass

from qililab.instruments.current_source import CurrentSource
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings import YokogawaGS200 as YokogawaGS200Driver
from qililab.typings.enums import Parameter, YokogawaSourceMode


@InstrumentFactory.register
class GS200(CurrentSource):
    """Yokogawa GS200 low voltage/current DC source.

    Args:
        name (InstrumentName): name of the instrument
        device (YokogawaGS200Driver): Instance of the qcodes GS200 class.
        settings (YokogawaGS200Settings): Settings of the instrument.
    """

    name = InstrumentName.YOKOGAWA_GS200

    @dataclass
    class YokogawaGS200Settings(CurrentSource.CurrentSourceSettings):
        """Contains the settings of a specific signal generator."""

        source_mode: YokogawaSourceMode = YokogawaSourceMode.CURRENT

    settings: YokogawaGS200Settings
    device: YokogawaGS200Driver

    @property
    def source_mode(self) -> YokogawaSourceMode:
        """Yokogawa GS200 `source_mode` property.

        Returns:
            str: settings.source_mode.
        """
        return self.settings.source_mode

    @source_mode.setter
    def source_mode(self, value: YokogawaSourceMode):
        """sets the source mode"""
        self.settings.source_mode = value
        self.device.source_mode(self.settings.source_mode.name[0:4])

    @property
    def current(self) -> float:
        """Yokogawa GS200 `current_value` property.

        Returns:
            float: settings.current_value.
        """
        return self.settings.current[0]

    @current.setter
    def current(self, value: float):
        """Sets the current_value"""
        self.settings.current[0] = value
        self.device.current(value)

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float | str | bool): new value
            channel_id (int | None): channel identifier of the parameter to update
        """
        if parameter == Parameter.SOURCE_MODE:
            self.source_mode = YokogawaSourceMode(value)
            return

        if parameter == Parameter.CURRENT:
            self.current = float(value)
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        self.source_mode = YokogawaSourceMode.CURRENT
        self.current = 0

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Dummy method."""
        self.device.on()

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop outputing current."""
        self.device.off()
