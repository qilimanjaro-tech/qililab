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

from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQPair, Waveform
from qililab.yaml import yaml


@yaml.register_class
class Measure(Operation):
    def __init__(
        self,
        bus: str,
        waveform: IQPair,
        weights: IQPair,
        warmup_pulse: IQPair | None = None,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: IQPair = waveform
        self.weights: IQPair = weights
        self.warmup_pulse: IQPair | None = warmup_pulse
        self.save_adc: bool = save_adc
        self.rotation: float | None = rotation
        self.demodulation: bool = demodulation

    def get_waveforms(self) -> tuple[Waveform, Waveform]:
        """Get the waveforms.

        Returns:
            tuple[Waveform, Waveform | None]: The waveforms as tuple.
        """
        wf_I: Waveform = self.waveform.I
        wf_Q: Waveform = self.waveform.Q
        return wf_I, wf_Q

    def get_warmup_duration(self) -> int:
        """Get the waveforms.

        Returns:
            tuple[Waveform, Waveform | None]: The warmup waveforms as tuple.
        """
        if self.warmup_pulse is not None:
            duration: int = self.warmup_pulse.I.get_duration()
            return duration
        return None


@yaml.register_class
class MeasureWithCalibratedWaveform(Operation):
    def __init__(
        self,
        bus: str,
        waveform: str,
        weights: IQPair,
        warmup_pulse: IQPair | None = None,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.weights: IQPair = weights
        self.warmup_pulse: IQPair | None = warmup_pulse
        self.save_adc: bool = save_adc
        self.rotation: float | None = rotation
        self.demodulation: bool = demodulation


@yaml.register_class
class MeasureWithCalibratedWeights(Operation):
    def __init__(
        self,
        bus: str,
        waveform: IQPair,
        weights: str,
        warmup_pulse: IQPair | None = None,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: IQPair = waveform
        self.weights: str = weights
        self.warmup_pulse: IQPair | None = warmup_pulse
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
        warmup_pulse: IQPair | None = None,
        save_adc: bool = False,
        rotation: float | None = None,
        demodulation: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.weights: str = weights
        self.warmup_pulse: IQPair | None = warmup_pulse
        self.save_adc: bool = save_adc
        self.rotation: float | None = rotation
        self.demodulation: bool = demodulation
