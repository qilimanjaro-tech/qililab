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

"""VoltageSource class."""

from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class VoltageSource(Instrument):
    """Abstract base class defining all instruments used to generate voltages."""

    @dataclass
    class VoltageSourceSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            voltage (list[float]): List of voltages of the instrument's DACs in V. Value range is (-40, 40).
            span (list[str]): A list of the max range of each DACs.
            ramping_enabled (list[bool]): A list of ramping enabled boolean values per DAC.
            ramp_rate (list[float]): List of ramping rates in mA / ms per DAC.
            dacs (list[int]): List of the dacs of which to set the current.
        """

        voltage: list[float]
        span: list[str]
        ramping_enabled: list[bool]
        ramp_rate: list[float]
        dacs: list[int]  # indices of the dacs to use

    settings: VoltageSourceSettings

    @property
    def voltage(self):
        """VoltageSource 'voltage' property.

        Returns:
            float: settings.voltage.
        """
        return self.settings.voltage

    @property
    def dacs(self):
        """CurrentSource 'dacs' property.

        Returns:
            int: settings.dacs
        """
        return self.settings.dacs

    @property
    def span(self):
        """VoltageSource 'span' property.

        Returns:
            float: settings.span.
        """
        return self.settings.span

    @property
    def ramping_enabled(self):
        """VoltageSource 'ramping_enabled' property.

        Returns:
            float: settings.ramping_enabled.
        """
        return self.settings.ramping_enabled

    @property
    def ramp_rate(self):
        """VoltageSource 'ramp_rate' property.

        Returns:
            float: settings.ramp_rate.
        """
        return self.settings.ramp_rate

    def to_dict(self):
        """Return a dict representation of the VoltageSource class."""
        return dict(super().to_dict().items())
