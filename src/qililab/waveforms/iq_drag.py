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

"""Waveform protocol class."""

from typing import Optional

import numpy as np

from qililab.qprogram.decorators import requires_domain
from qililab.qprogram.variable import Domain
from qililab.waveforms.arbitrary import Arbitrary
from qililab.waveforms.drag_correction import DragCorrection
from qililab.waveforms.gaussian import Gaussian
from qililab.waveforms.iq_waveform import IQWaveform
from qililab.waveforms.waveform import Waveform
from qililab.yaml import yaml


@yaml.register_class
class IQDrag(IQWaveform):
    @requires_domain("amplitude", Domain.Voltage)
    @requires_domain("duration", Domain.Time)
    @requires_domain("num_sigmas", Domain.Scalar)
    @requires_domain("drag_coefficient", Domain.Scalar)
    def __init__(self, 
                 amplitude: float,
                 duration: int,
                 num_sigmas: float,
                 drag_coefficient: float, *,
                 angle: float = np.pi,
                 phase: float = 0):

        self.amplitude = amplitude
        self.duration = duration
        self.num_sigmas = num_sigmas
        self.drag_coefficient = drag_coefficient
        self.angle = (angle + np.pi) % (2 * np.pi) - np.pi
        if self.angle < 0:
            self.angle = -self.angle
            self.phase = (phase) % (2 * np.pi) - np.pi
        else:
            self.phase = (phase + np.pi) % (2 * np.pi) - np.pi
        self.I: Optional[Waveform] = None
        self.Q: Optional[Waveform] = None

    def _compute_waveform(self) -> None:
        c, s = np.cos(self.phase), np.sin(self.phase)
        scale = self.angle / np.pi

        gausian = Gaussian(
            amplitude=self.amplitude,
            duration=self.duration,
            num_sigmas=self.num_sigmas
            )

        drag_correction = DragCorrection(
            waveform=gausian,
            drag_coefficient=self.drag_coefficient,
            ).envelope()

        gausian = gausian.envelope()

        self.I = Arbitrary(scale * (gausian * c - drag_correction * s))
        self.Q = Arbitrary(scale * (gausian * s + drag_correction * c))

    def get_I(self) -> Waveform:
        if self.I is None:
            self._compute_waveform()
        return self.I

    def get_Q(self) -> Waveform:
        if self.Q is None:
            self._compute_waveform()
        return self.Q

    def get_duration(self) -> int:
        return self.duration
