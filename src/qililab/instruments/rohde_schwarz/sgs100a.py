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
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""

from dataclasses import dataclass

from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue, RohdeSchwarzSGS100A


@InstrumentFactory.register
class SGS100A(Instrument):
    """Rohde & Schwarz SGS100A class

    Args:
        name (InstrumentName): name of the instrument
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    name = InstrumentName.ROHDE_SCHWARZ

    @dataclass
    class SGS100ASettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            power (float): Power of the instrument. Value range is (-120, 25).
            frequency (float): Frequency of the instrument. Value range is (1e6, 20e9).
        """

        power: float
        frequency: float
        rf_on: bool
        iq_wideband: bool = True
        alc: bool = True

    settings: SGS100ASettings
    device: RohdeSchwarzSGS100A

    @property
    def power(self):
        """SignalGenerator 'power' property.

        Returns:
            float: settings.power.
        """
        return self.settings.power

    @property
    def frequency(self):
        """SignalGenerator 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency

    @property
    def rf_on(self):
        """SignalGenerator 'rf_on' property.
        Returns:
            bool: settings.rf_on.
        """
        return self.settings.rf_on

    @property
    def iq_wideband(self):
        """SignalGenerator "I/Q wideband" property.
        Returns:
            bool: settings.iq_wideband.
        """
        return self.settings.iq_wideband

    @property
    def alc(self):
        """SignalGenerator "Automatic Level Control" property.
        Returns:
            bool: settings.alc.
        """
        return self.settings.alc

    def to_dict(self):
        """Return a dict representation of the SignalGenerator class."""
        return dict(super().to_dict().items())

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None):
        """Set R&S dbm power and frequency. Value ranges are:
        - power: (-120, 25).
        - frequency (1e6, 20e9).
        """
        if parameter == Parameter.POWER:
            self.settings.power = float(value)
            if self.is_device_active():
                self.device.power(self.power)
            return
        if parameter == Parameter.LO_FREQUENCY:
            self.settings.frequency = float(value)
            if self.is_device_active():
                self.device.frequency(self.frequency)
            return
        if parameter == Parameter.RF_ON:
            value = bool(value)
            if self.is_device_active():
                if value:
                    self.turn_on()
                else:
                    self.turn_off()
            return
        if parameter == Parameter.ALC:
            self.settings.alc = bool(value)
            if self.is_device_active():
                status = "Table & On"
                if not value:
                    status = "Off"
                self.device.send_command(command=":SOUR:POW:ALC:STAT", arg=status)
            return
        if parameter == Parameter.IQ_WIDEBAND:
            self.settings.iq_wideband = bool(value)
            if self.is_device_active():
                status = 1
                if not value:
                    status = 0
                self.device.send_command(command="SOUR:IQ:WBST", arg=status)
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None) -> ParameterValue:
        if parameter == Parameter.POWER:
            return self.settings.power
        if parameter == Parameter.LO_FREQUENCY:
            return self.settings.frequency
        if parameter == Parameter.RF_ON:
            return self.settings.rf_on
        if parameter == Parameter.ALC:
            return self.settings.alc
        if parameter == Parameter.IQ_WIDEBAND:
            return self.settings.iq_wideband
        raise ParameterNotFound(self, parameter)

    def get_rs_options(self):
        """Returns the options of the R&S
        Returns:
            str: The query returns a list of options. The options are returned at fixed positions in a comma-separated string. A zero is returned for options that are not installed.
        """
        return self.device.ask(command="*OPT?")

    @check_device_initialized
    def initial_setup(self):
        """performs an initial setup"""
        self.device.power(self.power)
        self.device.frequency(self.frequency)
        if not self.alc:
            self.device.send_command(command=":SOUR:POW:ALC:STAT", arg="Off")
        if not self.iq_wideband:
            self.device.send_command(command="SOUR:IQ:WBST", arg=0)
        if self.rf_on:
            self.device.on()
        else:
            self.device.off()

    @check_device_initialized
    def turn_on(self):
        """Start generating microwaves."""
        self.settings.rf_on = True
        self.device.on()

    @check_device_initialized
    def turn_off(self):
        """Stop generating microwaves."""
        self.settings.rf_on = False
        self.device.off()

    @check_device_initialized
    def reset(self):
        """Reset instrument."""
