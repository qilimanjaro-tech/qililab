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

from dataclasses import dataclass, field

from qililab.pulse_distortion import PulseDistortion
from qililab.typings import ChannelID


@dataclass
class BusSettings:
    """Dataclass with all the settings the buses of the platform need.
    Args:
        alias (str): Alias of the bus.
        system_control (dict): Dictionary containing the settings of the system control of the bus.
        distortions (list[dict]): List of dictionaries containing the settings of the distortions applied to each
            bus.
        delay (int, optional): Delay applied to all pulses sent in this bus. Defaults to 0.
    """

    alias: str
    instruments: list[str]
    channels: list[ChannelID | None]
    delay: int = 0
    distortions: list[PulseDistortion] = field(default_factory=list)
