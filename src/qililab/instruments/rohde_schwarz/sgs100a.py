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

import warnings
from dataclasses import dataclass

from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue, RohdeSchwarzSGS100A, ModuleID


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
        rf_on: bool = True
        alc: bool = True
        iq_modulation: bool = False
        iq_wideband: bool = True
        operation_mode: str = "normal"

    settings: SGS100ASettings
    device: RohdeSchwarzSGS100A
    freq_top_limit: float
    freq_bot_limit: float
    device_initialized: bool = False

    @property
    def power(self):
        """SignalGenerator 'power' property.

        Returns:
            float: settings.power.
        """
        if self.device_initialized:
            if not -120 <= self.settings.power <= 25:
                raise ValueError(
                    f"Value set for power is outside of the allowed range [-120,25]: {self.settings.power}"
                )
        return self.settings.power

    @property
    def frequency(self):
        """SignalGenerator 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        if self.device_initialized:
            if not self.freq_bot_limit <= self.settings.frequency <= self.freq_top_limit:
                raise ValueError(
                    f"Value set for frequency is outside of the allowed range [{self.freq_bot_limit}, {self.freq_top_limit}]: {self.settings.frequency}"
                )
        return self.settings.frequency

    @property
    def rf_on(self):
        """SignalGenerator 'rf_on' property.
        Returns:
            bool: settings.rf_on.
        """
        return self.settings.rf_on

    @property
    def alc(self):
        """SignalGenerator "Automatic Level Control" property.
        Returns:
            bool: settings.alc.
        """
        return self.settings.alc

    @property
    def iq_modulation(self):
        """SignalGenerator 'IQ state' property.
        Returns:
            bool: settings.iq_modulation.
        """
        return self.settings.iq_modulation

    @property
    def iq_wideband(self):
        """SignalGenerator "I/Q wideband" property.
        Returns:
            bool: settings.iq_wideband.
        """
        return self.settings.iq_wideband

    @property
    def operation_mode(self):
        """SignalGenerator "Operation Mode" property.
        Returns:
            str: settings.operation_mode.
        """
        return self.settings.operation_mode

    def to_dict(self):
        """Return a dict representation of the SignalGenerator class."""
        return dict(super().to_dict().items())

    @log_set_parameter
    def set_parameter(
        self,
        parameter: Parameter,
        value: ParameterValue,
        channel_id: ChannelID | None = None,
        module_id: ModuleID | None = None,
    ):
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
            self.settings.rf_on = bool(value)
            if self.is_device_active():
                if value:
                    self.turn_on()
                else:
                    self.turn_off()
            return
        if parameter == Parameter.ALC:
            self.settings.alc = bool(value)
            if self.is_device_active():
                status = "ONT"
                if not value:
                    status = "OFF"
                self.device.write(f":SOUR:POW:ALC:STAT {status}")
            return
        if parameter == Parameter.IQ_WIDEBAND:
            self.settings.iq_wideband = bool(value)
            if self.is_device_active():
                status = str(1)
                if not value:
                    status = str(0)
                self.device.write(f"SOUR:IQ:WBST {status}")
            return
        if parameter == Parameter.IQ_MODULATION:
            self.settings.iq_modulation = bool(value)
            if self.is_device_active():
                self.device.IQ_state(self.iq_modulation)
            return
        if parameter == Parameter.OPERATION_MODE:
            value = str(value).lower()
            if value not in ("normal", "bypass"):
                raise ParameterNotFound(self, parameter)
            self.settings.operation_mode = value
            if self.is_device_active():
                operation_mode = "NORMal" if value == "normal" else "BBBYpass"
                self.device.write(f":SOUR:OPMode {operation_mode}")
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(
        self,
        parameter: Parameter,
        channel_id: ChannelID | None = None,
        module_id: ModuleID | None = None,
    ) -> ParameterValue:
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
        if parameter == Parameter.IQ_MODULATION:
            return self.settings.iq_modulation
        if parameter == Parameter.OPERATION_MODE:
            return self.settings.operation_mode
        raise ParameterNotFound(self, parameter)

    @check_device_initialized
    def get_rs_options(self):
        """Returns the options of the R&S
        Returns:
            str: The query returns a list of options. The options are returned at fixed positions in a comma-separated string. A zero is returned for options that are not installed.
        """
        return self.device.ask("*OPT?")

    @check_device_initialized
    def initial_setup(self):
        """performs an initial setup"""
        self.device_initialized = True
        device_mixer = self.get_rs_options().split(",")[-1]
        if device_mixer == "SGS-B112" or device_mixer == "SGS-B112V":
            self.freq_top_limit = 12.75e9
        elif device_mixer == "SGS-B106" or device_mixer == "SGS-B106V":
            self.freq_top_limit = 6e9
        if device_mixer == "SGS-B112" or device_mixer == "SGS-B106":
            self.freq_bot_limit = 1e6
        elif device_mixer == "SGS-B112V" or device_mixer == "SGS-B106V":
            self.freq_bot_limit = 80e6
        self.device.power(self.power)
        self.device.frequency(self.frequency)
        if self.alc:
            self.device.write(":SOUR:POW:ALC:STAT ONT")
        else:
            self.device.write(":SOUR:POW:ALC:STAT OFF")
        if device_mixer == "SGS-B112V" and self.iq_modulation:
            self.device.IQ_state(self.iq_modulation)
            if self.iq_wideband:
                if self.frequency < 2.5e9:
                    warnings.warn(
                        f"LO frequency below 2.5GHz only allows for IF sweeps of ±{self.frequency * 0.2:,.2e} Hz",
                        ResourceWarning,
                    )
                self.device.write("SOUR:IQ:WBST 1")
            else:
                if self.frequency < 1e9:
                    freq = self.frequency * 0.05
                    warnings.warn(
                        f"Deactivated wideband & LO frequency below 1GHz allows for IF sweeps of ±{freq:,.2e} Hz",
                        ResourceWarning,
                    )
                else:
                    warnings.warn("Deactivated wideband allows for IF sweeps of ±50e6 Hz", ResourceWarning)
                self.device.write("SOUR:IQ:WBST 0")
        elif not self.iq_modulation:
            self.device.IQ_state(self.iq_modulation)
        if self.rf_on:
            self.device.on()
        else:
            self.device.off()
        if self.operation_mode in ("normal", "bypass"):
            operation_mode = "NORMal" if self.operation_mode == "normal" else "BBBYpass"
            self.device.write(f":SOUR:OPMode {operation_mode}")
        else:
            warnings.warn(
                f"Operation mode '{self.operation_mode}' not allowed, defaulting to normal operation mode",
                ResourceWarning
            )
            self.settings.operation_mode = "normal"
            self.device.write(":SOUR:OPMode NORMal")

    @check_device_initialized
    def turn_on(self):
        """Start generating microwaves."""
        if not self.settings.rf_on:
            self.device.off()  # this avoids the initialisation to overwrite the runcard
        else:
            self.device.on()

    @check_device_initialized
    def turn_off(self):
        """Stop generating microwaves."""
        self.settings.rf_on = False
        self.device.off()

    @check_device_initialized
    def reset(self):
        """Reset instrument."""
