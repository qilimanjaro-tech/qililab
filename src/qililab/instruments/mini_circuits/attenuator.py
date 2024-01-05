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

"""Attenuator class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter
from qililab.typings.instruments.mini_circuits import MiniCircuitsDriver


@InstrumentFactory.register
class Attenuator(Instrument):
    """Attenuator class.

    Args:
        name (InstrumentName): name of the instrument
        device (MiniCircuitsDriver): Instance of the MiniCircuitsDriver class.
        settings (StepAttenuatorSettings): Settings of the instrument.
    """

    name = InstrumentName.MINI_CIRCUITS

    @dataclass
    class StepAttenuatorSettings(Instrument.InstrumentSettings):
        """Step attenuator settings."""

        attenuation: float

    settings: StepAttenuatorSettings
    device: MiniCircuitsDriver

    @Instrument.CheckParameterValueFloatOrInt
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):  # type: ignore
        """Set instrument settings."""
        if parameter == Parameter.ATTENUATION:
            self.settings.attenuation = float(value)
            if self.is_device_active():
                self.device.setup(attenuation=self.attenuation)
            return
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        self.device.setup(attenuation=self.attenuation)

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Turn off an instrument."""

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turn on an instrument."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""

    @property
    def attenuation(self):
        """Attenuator 'attenuation' property.

        Returns:
            float: Attenuation.
        """
        return self.settings.attenuation
