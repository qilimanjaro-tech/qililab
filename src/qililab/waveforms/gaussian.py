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

import numpy as np

from .waveform import Waveform


class Gaussian(Waveform):  # pylint: disable=too-few-public-methods
    """Gaussian waveform with peak at duration/2 and spanning for num_sigmas over the pule duration.

    The normal distribution's parameters mu (mean) and sigma (standard deviation) will be therefore
    defined by mu = duration / 2 and sigma = duration / num_sigmas
    """

    def __init__(self, amplitude: float, duration: int, num_sigmas: float):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
            num_sigmas (float): number of sigmas in the gaussian pulse
        """

        self.amplitude = amplitude
        self.duration = duration
        self.num_sigmas = num_sigmas

    def envelope(self, resolution: float = 1):
        """Returns the pulse matrix

        Args:
            resolution (int, optional): Pulse resolution. Defaults to 1.

        Returns:
            np.ndarray: pulse matrix
            resolution (int, optional): Pulse resolution. Defaults to 1.
        """
        sigma = self.duration / self.num_sigmas
        mu = self.duration / 2
        x = np.arange(self.duration / resolution) * resolution

        gaussian = self.amplitude * np.exp(-0.5 * (x - mu) ** 2 / sigma**2)
        norm = np.amax(np.real(gaussian))

        gaussian = gaussian - gaussian[0]  # Shift to avoid introducing noise at time 0
        corr_norm = np.amax(np.real(gaussian))

        return gaussian * norm / corr_norm if corr_norm != 0 else gaussian
