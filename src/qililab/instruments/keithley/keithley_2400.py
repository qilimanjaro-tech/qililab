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
import time

import numpy as np

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import ChannelID, InstrumentName, Keithley2400Driver, OutputID, Parameter, ParameterValue


@InstrumentFactory.register
class Keithley2400(Instrument):
    """Keithley2600 class.
    Args:
        name (InstrumentName): name of the instrument
        device (Keithley2400Driver): Instance of the Instrument device driver.
        settings (Keithley2400Settings): Settings of the instrument.
    """

    name = InstrumentName.KEITHLEY2600

    @dataclass
    class Keithley2400Settings(Instrument.InstrumentSettings):
        """Settings for Keithley2600 instrument."""

        mode: str
        output: bool = True
        current: float | None = None
        voltage: float | None = None

    settings: Keithley2400Settings
    device: Keithley2400Driver

    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None):
        """Setup instrument."""
        if parameter == Parameter.CURRENT:
            self.current = float(value)
            if self.is_device_active():
                self.device.mode('CURR')
                self.device.output(True)
                self.device.curr(self.current)
            return
        if parameter == Parameter.VOLTAGE:
            self.voltage = float(value)
            if self.is_device_active():
                self.device.mode('VOLT')
                self.device.output(True)
                self.device.volt(self.voltage)
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(
        self, parameter: Parameter, channel_id: ChannelID | None = None, output_id: OutputID | None = None
    ):
        """Setup instrument."""
        if parameter == Parameter.CURRENT:
            if self.mode == "VOLT" and self.is_device_active():
                self.current = self.device.curr()
            return self.current
        if parameter == Parameter.VOLTAGE:
            if self.mode == "CURR" and self.is_device_active():
                self.voltage = self.device.volt()
            return self.voltage
            
        raise ParameterNotFound(self, parameter)

    def initial_setup(self):
        """performs an initial setup"""
        self.device.mode(self.mode)
        self.device.output(self.output)
        if self.mode == "VOLT":
            if not self.voltage:
                raise ValueError("Mode set to VOLTage but no voltage given.")
            self.device.volt(self.voltage)
        elif self.mode == "CURR":
            if not self.current:
                raise ValueError("Mode set to CURRent but no current given.")
            self.device.curr(self.current)
        else:
            raise ValueError("Mode has to be either CURR (current) or Volt (voltage).")

    def turn_on(self):
        """Turn on an instrument."""

    def turn_off(self):
        """Turn off an instrument."""

    def reset(self):
        """Reset instrument."""
        self.device.reset()

    def fast_sweep(self, data_sweep: list | np.ndarray, time_interval: float) -> tuple[str, np.ndarray, np.ndarray]:
        """Perform a fast sweep using a data list and return the dataset.

        Args:
            data_sweep(list | np.ndarray): sweep list for either Voltage or Current (V or A)
            time_interval: waiting time between measurements (in seconds)

        Returns:
            str: data type returned.
            np.ndarray: Measurement time interval.
            np.ndarray: Measured voltage or current.
        """
        data_type = "Voltage (V)" if self.mode == "CURR" else "Current (A)"
        measured_data = np.zeros(np.array(data_sweep).shape)
        time_sweep = np.zeros(np.array(data_sweep).shape)

        for ii, value in enumerate(data_sweep):
            if self.mode == "VOLT":
                self.voltage(value)
                measured_data[ii] = self.current
            if self.mode == "CURR":
                self.current(value)
                measured_data[ii] = self.voltage()
            time.sleep(time_interval)
            time_sweep[ii] = time.time()
        return data_type, time_sweep, measured_data

    @property
    def mode(self):
        """Keithley2400 'mode' property.

        Returns:
            str: Mode of the instrument.
        """
        return self.settings.mode

    @property
    def output(self):
        """Keithley2400 'output' property.

        Returns:
            bool: Output of the instrument.
        """
        return self.settings.output

    @property
    def current(self):
        """Keithley2400 'current' property.

        Returns:
            float: Current in current (set) or voltage (get) mode.
        """
        if self.mode == "VOLT" and self.is_device_active():
            return self.device.curr()
        elif self.mode == "CURR":
            return self.settings.current

    @current.setter
    def current(self, value: float):
        """Keithley2400 'current' setter property.

        Args:
            float: Current in current (set) mode.
        """
        if self.mode == "VOLT":
            raise ValueError("VOLTage mode set but current given.")
        elif self.mode == "CURR" and self.is_device_active():
            self.device.curr(value)

    @property
    def voltage(self):
        """Keithley2400 'voltage' property.

        Returns:
            float: Voltage in current (get) or voltage (set) mode.
        """
        if self.mode == "VOLT":
            return self.settings.voltage
        elif self.mode == "CURR" and self.is_device_active():
            return self.device.volt()

    @voltage.setter
    def voltage(self, value: float):
        """Keithley2400 'voltage' setter property.

        Args:
            float: Voltage in voltage (set) mode.
        """
        if self.mode == "VOLT" and self.is_device_active():
            self.device.volt(value)
        elif self.mode == "CURR":
            raise ValueError("CURRent mode set but voltage given.")
