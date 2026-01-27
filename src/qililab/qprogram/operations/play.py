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


from qililab.waveforms import IQWaveform, Waveform
from qililab.yaml import yaml

from . import Operation, SdkPlay


@yaml.register_class
class Play(SdkPlay):
    def __init__(
        self,
        bus: str,
        waveform: Waveform | IQWaveform,
        wait_time: int | None = None,
        dwell: int | None = None,
        delay: int | None = None,
        repetitions: int | None = None,
    ) -> None:
        super().__init__(bus=bus, waveform=waveform)
        self.wait_time: int | None = wait_time
        self.dwell: int | None = dwell
        self.delay: int | None = delay
        self.repetitions: int | None = repetitions


@yaml.register_class
class PlayWithCalibratedWaveform(Operation):
    def __init__(
        self,
        bus: str,
        waveform: str,
        wait_time: int | None = None,
        dwell: int | None = None,
        delay: int | None = None,
        repetitions: int | None = None,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.wait_time: int | None = wait_time
        self.dwell: int | None = dwell
        self.delay: int | None = delay
        self.repetitions: int | None = repetitions
