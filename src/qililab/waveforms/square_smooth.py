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

"""Square waveform."""

import numpy as np
from scipy.special import erf

from qililab.qprogram.decorators import requires_domain
from qililab.qprogram.variable import Domain
from qililab.yaml import yaml

from .waveform import Waveform


@yaml.register_class
class SquareSmooth(Waveform):
    """Smoothed square pulse with error function on the edges rise waveform.

    Args:
        duration (int): Duration of the pulse (ns).
        amplitude (float): Maximum amplitude of the pulse.
        smooth_duration (float, optional): duration of the smoothing component. Defaults to 0.5.
        buffer (float, optional): Buffer of the waveform. Defaults to 3.0.
    """

    @requires_domain("amplitude", Domain.Voltage)
    @requires_domain("duration", Domain.Time)
    def __init__(self, amplitude: float, duration: int, smooth_duration: int, buffer: int = 0):
        super().__init__()
        self.amplitude = amplitude
        self.duration = duration
        self.smooth_duration = smooth_duration
        self.buffer = buffer

    def envelope(self, resolution: int = 1) -> np.ndarray:
        """Smoothed square pulse with error function on the edges rise envelope.

        Args:
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            np.ndarray: Height of the envelope for each time step.
        """
        x = np.arange(0, self.duration, resolution)
        A = self.amplitude
        err = self.smooth_duration / 2
        buf = self.buffer
        dur = self.duration - 1
        return 0.5 * A * np.real((erf((x - buf) / err) - erf((x - dur + buf) / err)))

    def get_duration(self) -> int:
        """Get the duration of the waveform.

        Returns:
            int: The duration of the waveform in ns.
        """
        return self.duration
