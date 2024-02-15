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

"""SNZ waveform."""
import numpy as np

from qililab.qprogram.decorators import requires_domain
from qililab.qprogram.variable import Domain

from .waveform import Waveform


# pylint: disable=anomalous-backslash-in-string
class SNZ(Waveform):  # pylint: disable=too-few-public-methods
    """Sudden Net Zero
    
    Args:
        amplitude (float): Maximum amplitude of the pulse.
        duration (int): Duration of the pulse (ns). Duration - t_phi must be an even number
        b (float): impulse after halfpulse
    """

    @requires_domain("amplitude", Domain.Voltage)
    @requires_domain("duration", Domain.Time)
    @requires_domain("b", Domain.Scalar)
    def __init__(self, amplitude: float, duration: int, b: float):
        super().__init__()
        self.amplitude = amplitude
        self.duration = duration
        self.b = b
        self.t_phi = 1
    
    def envelope(self, resolution: int = 1) -> np.ndarray:
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.

        The duration of the each half-pulse is determined by the total pulse duration. Thus
        halfpulse_t = (duration - t_phi - 2) / 2. This implies that (duration - t_phi) should be even.
        The -2 in the formula above is due to the 2 impulses b.
        """
        # calculate the halfpulse duration
        halfpulse_t = (self.duration - 2 - self.t_phi) / 2
        halfpulse_t = int(halfpulse_t / resolution)

        envelope = np.empty(round(self.duration / resolution))
        # raise warning if we are rounding
        envelope[:halfpulse_t] = self.amplitude * np.ones(halfpulse_t)  # positive square halfpulse
        envelope[halfpulse_t] = self.b * self.amplitude  # impulse b
        envelope[halfpulse_t + 2 + self.t_phi :] = 0  # t_phi
        envelope[halfpulse_t + 1 + self.t_phi] = -self.b * self.amplitude  # impulse -b
        envelope[halfpulse_t + 2 + self.t_phi :] = -self.amplitude * np.ones(halfpulse_t)  # negative square halfpulse

        return envelope

    def get_duration(self) -> int:
        """Get the duration of the waveform.

        Returns:
            int: The duration of the waveform in ns.
        """
        return self.duration
