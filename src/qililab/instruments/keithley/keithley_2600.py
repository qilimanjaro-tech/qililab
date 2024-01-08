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

"""Keithley2600 instrument."""
from dataclasses import dataclass

import numpy as np

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, Keithley2600Driver
from qililab.typings.enums import Parameter


@InstrumentFactory.register
class Keithley2600(Instrument):
    """Keithley2600 class.
    Args:
        name (InstrumentName): name of the instrument
        device (Keithley2600Driver): Instance of the Instrument device driver.
        settings (Keithley2600Settings): Settings of the instrument.
    """

    name = InstrumentName.KEITHLEY2600

    @dataclass
    class Keithley2600Settings(Instrument.InstrumentSettings):
        """Settings for Keithley2600 instrument."""

        max_current: float
        max_voltage: float

    settings: Keithley2600Settings
    device: Keithley2600Driver

    @Instrument.CheckParameterValueFloatOrInt
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):  # type: ignore
        """Setup instrument."""
        if parameter == Parameter.MAX_CURRENT:
            self.max_current = float(value)
            if self.is_device_active():
                self.device.smua.limiti(self.max_current)
            return
        if parameter == Parameter.MAX_VOLTAGE:
            self.max_voltage = float(value)
            if self.is_device_active():
                self.device.smua.limitv(self.max_voltage)
            return
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup"""
        self.device.smua.limiti(self.max_current)
        self.device.smua.limitv(self.max_voltage)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turn on an instrument."""

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Turn off an instrument."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.device.reset()

    def fast_sweep(self, start: float, stop: float, steps: int, mode: str) -> tuple[np.ndarray, np.ndarray]:
        """Perform a fast sweep using a deployed lua script and return an xarray dataset.

        Args:
            start: starting sweep value (V or A)
            stop: end sweep value (V or A)
            steps: number of steps
            mode: Type of sweep, either 'IV' (voltage sweep), 'VI' (current sweep two probe setup) or 'VIfourprobe'
            (current sweep four probe setup)

        Returns:
            np.ndarray: Measured data.
        """
        data = self.device.smua.doFastSweep(start=start, stop=stop, steps=steps, mode=mode)
        x_values = np.linspace(start=start, stop=stop, num=steps)
        return x_values, data.to_xarray().to_array().values.squeeze()

    @property
    def max_current(self):
        """Keithley2600 'max_current' property.

        Returns:
            float: Maximum current allowed in voltage mode.
        """
        return self.settings.max_current

    @max_current.setter
    def max_current(self, value: float):
        """Keithley2600 'max_current' setter property.

        Args:
            float: Maximum current allowed in voltage mode.
        """
        if self.is_device_active():
            self.device.smua.limiti(value)
        self.settings.max_current = value

    @property
    def max_voltage(self):
        """Keithley2600 'max_voltage' property.

        Returns:
            float: Maximum voltage allowed in current mode.
        """
        return self.settings.max_voltage

    @max_voltage.setter
    def max_voltage(self, value: float):
        """Keithley2600 'max_voltage' setter property.

        Args:
            float: Maximum voltage allowed in current mode.
        """
        if self.is_device_active():
            self.device.smua.limitv(value)
        self.settings.max_voltage = value
