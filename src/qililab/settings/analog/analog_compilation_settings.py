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

from dataclasses import asdict, dataclass, field

from qililab.settings.analog.flux_control_topology import FluxControlTopology


@dataclass
class AnalogCompilationSettings:
    """Dataclass with all the settings and gates definitions needed to decompose gates into pulses."""

    flux_control_topology: list[FluxControlTopology] = field(default_factory=list)

    def __post_init__(self):
        """Build the Gates Settings based on the master settings."""
        self.flux_control_topology = [
            FluxControlTopology(**flux_control) if isinstance(flux_control, dict) else flux_control
            for flux_control in self.flux_control_topology
        ]

    def to_dict(self):
        """Serializes gate settings to dictionary and removes fields with None values"""

        return asdict(self)
