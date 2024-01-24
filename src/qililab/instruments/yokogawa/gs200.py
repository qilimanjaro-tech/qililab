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

"""Yokogawa GS200 Instrument"""
from dataclasses import dataclass

from qililab.instruments.current_source import CurrentSource
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import InstrumentName
from qililab.typings import YokogawaGS200 as YokogawaGS200Driver
from qililab.typings.enums import Parameter, SourceMode


@InstrumentFactory.register
class GS200(CurrentSource, VoltageSource):
    """Yokogawa GS200 low voltage/current DC source.

    Args:
        name (InstrumentName): name of the instrument
        device (YokogawaGS200Driver): Instance of the qcodes GS200 class.
        settings (YokogawaGS200Settings): Settings of the instrument.
    """

    name = InstrumentName.YOKOGAWA_GS200

    @dataclass
    class YokogawaGS200Settings(CurrentSource.CurrentSourceSettings, VoltageSource.VoltageSourceSettings):
        """Contains the settings of a specific signal generator."""

        source_mode: SourceMode

    settings: YokogawaGS200Settings
    device: YokogawaGS200Driver

    @property
    def source_mode(self) -> SourceMode:
        """Yokogawa GS200 `source_mode` property. It determines if the instrument will act as Current Source or Voltage Source.

        Returns:
            SourceMode: The source mode of the instrument.
        """
        return self.settings.source_mode

    @source_mode.setter
    def source_mode(self, value: SourceMode):
        """Set the Yokogawa GS200 source mode."""
        self.settings.source_mode = value
        if self.is_device_active():
            qcodes_str = self.__source_mode_to_qcodes_str(value)
            self.device.source_mode(qcodes_str)

    @property
    def ramping_enabled(self):
        """Yokogawa GS200 'ramping_enabled' property. If set to True, changes in current will transition linearly according to the `ramping_rate` value.

        Returns:
            bool: True, if ramping is enabled.
        """
        return self.settings.ramping_enabled[0]

    @ramping_enabled.setter
    def ramping_enabled(self, value: bool):
        """Set the Yokogawa `ramping_enabled` property."""
        self.settings.ramping_enabled[0] = value

    @property
    def ramping_rate(self):
        """Yokogawa GS200 'ramping_rate' property. If `ramping_enabled` is set to True, changes in current will transition linearly according to this value.

        Returns:
            float: The ramping rate in mA/ms or mV/ms.
        """
        return self.settings.ramp_rate[0]

    @ramping_rate.setter
    def ramping_rate(self, value: float):
        """Set the Yokogawa GS200 `ramping_rate` property."""
        self.settings.ramp_rate[0] = value

    @property
    def current(self) -> float:
        """Yokogawa GS200 `current` property.

        Returns:
            float: The current of the instrument in A.
        """
        return self.settings.current[0]

    @current.setter
    def current(self, value: float):
        """Set Yokogawa GS200 `current` property. If `ramping_enabled` is set to True, the current will transition linearly according to `ramping_rate`. Else, it will be set instantly."""
        self.settings.current[0] = value
        if self.is_device_active():
            if self.ramping_enabled:
                self.device.ramp_current(value, self.ramping_rate * 0.001, 0.001)
            else:
                self.device.current(value)

    @property
    def span(self) -> str:
        """Yokogawa GS200 `span` property.

        Returns:
            str: The span of the instrument.
        """
        return self.settings.span[0]

    @span.setter
    def span(self, value: str):
        """Set Yokogawa GS200 `span` property.

        Available values:
            - 10mV
            - 100mV
            - 1V
            - 10V
            - 30V
            - 1mA
            - 10mA
            - 100mA
            - 200mA
        """
        self.settings.span[0] = value
        if self.is_device_active():
            if self.source_mode == SourceMode.CURRENT:
                qcodes_int = self.__current_span_to_qcodes_float(value)
                self.device.current_range(qcodes_int)
            else:
                qcodes_int = self.__voltage_span_to_qcodes_float(value)
                self.device.voltage_range(qcodes_int)

    @property
    def voltage(self) -> float:
        """Yokogawa GS200 `voltage` property.

        Returns:
            float: The voltage of the instrument in V.
        """
        return self.settings.voltage[0]

    @voltage.setter
    def voltage(self, value: float):
        """Set Yokogawa GS200 `voltage` property. If `ramping_enabled` is set to True, the voltage will transition linearly according to `ramping_rate`. Else, it will be set instantly."""
        self.settings.voltage[0] = value
        if self.is_device_active():
            if self.ramping_enabled:
                self.device.ramp_voltage(value, self.ramping_rate * 0.001, 0.001)
            else:
                self.device.voltage(value)

    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float | str | bool): new value
            channel_id (int | None): channel identifier of the parameter to update
        """
        if parameter == Parameter.CURRENT:
            self.current = float(value)
            return

        if parameter == Parameter.VOLTAGE:
            self.voltage = float(value)
            return

        if parameter == Parameter.RAMPING_ENABLED:
            self.ramping_enabled = bool(value)
            return

        if parameter == Parameter.RAMPING_RATE:
            self.ramping_rate = float(value)
            return

        if parameter == Parameter.SOURCE_MODE:
            self.source_mode = SourceMode(value)
            return

        if parameter == Parameter.SPAN:
            self.span = str(value)
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Performs an initial setup."""
        self.device.off()
        self.source_mode = self.settings.source_mode
        self.span = self.settings.span[0]
        self.ramping_rate = self.settings.ramp_rate[0]
        self.ramping_enabled = self.settings.ramping_enabled[0]
        if self.source_mode == SourceMode.CURRENT:
            self.current = self.settings.current[0]
        else:
            self.voltage = self.settings.voltage[0]

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Start outputting current."""
        self.device.on()

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop outputing current."""
        self.device.off()

    def __source_mode_to_qcodes_str(self, source_mode: SourceMode) -> str:
        mapping = {SourceMode.CURRENT: "CURR", SourceMode.VOLTAGE: "VOLT"}
        return mapping[source_mode]

    def __voltage_span_to_qcodes_float(self, voltage_span: str) -> float:
        mapping = {"10mV": 10e-3, "100mV": 100e-3, "1V": 1e0, "10V": 10e0, "30V": 30e0}
        return mapping[voltage_span]

    def __current_span_to_qcodes_float(self, current_span: str) -> float:
        mapping = {"1mA": 1e-3, "10mA": 10e-3, "100mA": 100e-3, "200mA": 200e-3}
        return mapping[current_span]
