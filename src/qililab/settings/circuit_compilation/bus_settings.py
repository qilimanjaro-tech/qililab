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

from dataclasses import dataclass

from qililab.pulse.pulse_distortion import PulseDistortion
from qililab.typings.enums import Line


@dataclass
class BusSettings:
    """Settings for a single gate event. A gate event is an element of a gate schedule, which is the
    sequence of gate events that define what a gate does (the pulse events it consists of).

    A gate event is made up of GatePulseSettings, which contains pulse specific information, and extra arguments
    (bus and wait_time) which are related to the context in which the specific pulse in GatePulseSettings is applied

    Attributes:
        bus (str): bus through which the pulse is to be sent. The string has to match that of the bus alias in the runcard
        pulse (GatePulseSettings): settings of the bus to be launched
        wait_time (int): time to wait w.r.t gate start time (taken as 0) before launching the pulse
    """

    line: Line
    qubits: list[int]
    distortions: list[PulseDistortion]
    delay: int = 0

    def __post_init__(self):
        self.distortions = [
            PulseDistortion.from_dict(distortion) for distortion in self.distortions if isinstance(distortion, dict)  # type: ignore[arg-type]
        ]