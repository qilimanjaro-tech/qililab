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

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, RohdeSchwarzSGS100A
from qililab.typings.enums import Parameter


@InstrumentFactory.register
class SGS100A(SignalGenerator):
    """Rohde & Schwarz SGS100A class

    Args:
        name (InstrumentName): name of the instrument
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    name = InstrumentName.ROHDE_SCHWARZ

    @dataclass
    class SGS100ASettings(SignalGenerator.SignalGeneratorSettings):
        """Contains the settings of a specific signal generator."""

    settings: SGS100ASettings
    device: RohdeSchwarzSGS100A

    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
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
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup"""
        self.device.power(self.power)
        self.device.frequency(self.frequency)
        if self.rf_on:
            self.device.on()
        else:
            self.device.off()

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Start generating microwaves."""
        self.settings.rf_on = True
        self.device.on()

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop generating microwaves."""
        self.settings.rf_on = False
        self.device.off()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
