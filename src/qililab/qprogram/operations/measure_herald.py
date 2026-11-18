# Copyright 2026 Qilimanjaro Quantum Tech
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

from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQWaveform
from qililab.yaml import yaml


@yaml.register_class
class MeasureHerald(Operation):
    def __init__(
        self,
        bus: str,
        waveform: IQWaveform,
        weights: IQWaveform,
        max_attempts: int = 50,
        trigger_address: int = 1,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: IQWaveform = waveform
        self.weights: IQWaveform = weights
        self.max_attempts: int = max_attempts
        self.trigger_address: int = trigger_address


@yaml.register_class
class MeasureHeraldCalibrated(Operation):
    def __init__(
        self,
        bus: str,
        waveform: str,
        weights: str,
        max_attempts: int = 50,
        trigger_address: int = 1,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.weights: str = weights
        self.max_attempts: int = max_attempts
        self.trigger_address: int = trigger_address
