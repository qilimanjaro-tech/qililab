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

from qililab.waveforms import IQWaveform
from qililab.yaml import yaml

from . import Operation, SdkMeasure


@yaml.register_class
class Measure(SdkMeasure):
    def __init__(
        self,
        bus: str,
        waveform: IQWaveform,
        weights: IQWaveform,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__(bus=bus, waveform=waveform, weights=weights)
        self.save_adc: bool = save_adc
        self.rotation: float | None = rotation
        self.demodulation: bool = demodulation


@yaml.register_class
class MeasureWithCalibratedWaveform(Operation):
    def __init__(
        self,
        bus: str,
        waveform: str,
        weights: IQWaveform,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.weights: IQWaveform = weights
        self.save_adc: bool = save_adc
        self.rotation: float | None = rotation
        self.demodulation: bool = demodulation


@yaml.register_class
class MeasureWithCalibratedWeights(Operation):
    def __init__(
        self,
        bus: str,
        waveform: IQWaveform,
        weights: str,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: IQWaveform = waveform
        self.weights: str = weights
        self.save_adc: bool = save_adc
        self.rotation: float | None = rotation
        self.demodulation: bool = demodulation


@yaml.register_class
class MeasureWithCalibratedWaveformWeights(Operation):
    def __init__(
        self,
        bus: str,
        waveform: str,
        weights: str,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.weights: str = weights
        self.save_adc: bool = save_adc
        self.rotation: float | None = rotation
        self.demodulation: bool = demodulation
