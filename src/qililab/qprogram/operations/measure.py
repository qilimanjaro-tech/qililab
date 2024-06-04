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

from qililab.qprogram.operations.operation import Operation
from qililab.waveforms import IQPair, Waveform


@dataclass(frozen=True)
class Measure(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    waveform: IQPair
    weights: IQPair
    rotation: float = 0.0
    demodulation: bool = True
    save_raw_adc: bool = False

    def get_waveforms(self) -> tuple[Waveform, Waveform]:
        """Get the waveforms.

        Returns:
            tuple[Waveform, Waveform | None]: The waveforms as tuple.
        """
        wf_I: Waveform = self.waveform.I
        wf_Q: Waveform = self.waveform.Q
        return wf_I, wf_Q

    def get_weights(self) -> tuple[Waveform, Waveform]:
        """Get the weights.

        Returns:
            tuple[Waveform, Waveform | None]: The weights as tuple.
        """
        wf_I: Waveform = self.weights.I
        wf_Q: Waveform = self.weights.Q
        return wf_I, wf_Q


@dataclass(frozen=True)
class MeasureWithNamedOperation(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    operation: str
    weights: IQPair
    rotation: float = 0.0
    demodulation: bool = True
    save_raw_adc: bool = False
