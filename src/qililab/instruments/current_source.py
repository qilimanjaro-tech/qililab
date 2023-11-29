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

"""CurrentSource class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class CurrentSource(Instrument):
    """Abstract base class defining all instruments used to generate currents."""

    @dataclass
    class CurrentSourceSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            current (list[float]): List of currents of the instrument's DACs in A. Value range is (-8, 8).
            span (list[str]): A list of the max range of each DACs.
            ramping_enabled (list[bool]): A list of ramping enabled boolean values per DAC.
            ramp_rate (list[float]): List of ramping rates in mA / ms per DAC.
            dacs (list[int]): List of the dacs of which to set the current.
        """

        current: list[float]
        span: list[str]
        ramping_enabled: list[bool]
        ramp_rate: list[float]
        dacs: list[int]

    settings: CurrentSourceSettings

    @property
    def current(self):
        """CurrentSource 'current' property.

        Returns:
            float: settings.current.
        """
        return self.settings.current

    @property
    def dacs(self):
        """CurrentSource 'dacs' property.

        Returns:
            int: settings.dacs
        """
        return self.settings.dacs

    @property
    def span(self):
        """CurrentSource 'span' property.

        Returns:
            float: settings.span.
        """
        return self.settings.span

    @property
    def ramping_enabled(self):
        """CurrentSource 'ramping_enabled' property.

        Returns:
            float: settings.ramping_enabled.
        """
        return self.settings.ramping_enabled

    @property
    def ramp_rate(self):
        """CurrentSource 'ramp_rate' property.

        Returns:
            float: settings.ramp_rate.
        """
        return self.settings.ramp_rate

    def to_dict(self):
        """Return a dict representation of the CurrentSource class."""
        return dict(super().to_dict().items())
