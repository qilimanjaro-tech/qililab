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


class Arbitrary(Waveform):  # pylint: disable=too-few-public-methods, disable=missing-class-docstring
    def __init__(self, samples: np.ndarray):
        self.samples = samples

    def envelope(self, resolution: int = 1) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        if resolution == 1:
            return self.samples
        else:
            cumsum = np.cumsum(self.samples)
            cumsum[resolution:] = cumsum[resolution:] - cumsum[:-resolution]
            moving_avg = cumsum[resolution - 1 :] / resolution

            # Scaling and shifting
            scale_factor = (self.samples.max() - self.samples.min()) / (moving_avg.max() - moving_avg.min())
            shift = self.samples.max() - moving_avg.max() * scale_factor
            scaled_avg = moving_avg * scale_factor + shift

            # Clamping
            clamped_avg = np.clip(scaled_avg, self.samples.min(), self.samples.max())

            return clamped_avg
