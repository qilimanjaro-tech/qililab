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

"""DragCorrection waveform."""
import numpy as np

from .gaussian import Gaussian
from .waveform import Waveform


class DragCorrection(Waveform):  # pylint: disable=too-few-public-methods
    """Calculates the first order drag correction of the imaginary (Ey) channel of a drive pulse. See https://arxiv.org/abs/0901.0534 (10).

    So far only implemented for Gaussian pulses.

    Args:
        drag_coefficient (float): drag coefficient
        waveform (Waveform): waveform on which the drag transformation is calculated
    """

    def __init__(self, drag_coefficient: float, waveform: Waveform):
        self.drag_coefficient = drag_coefficient
        self.waveform = waveform

    def envelope(self, resolution: float = 1.0) -> np.ndarray:
        """Returns the envelope corresponding to the drag correction.

        Args:
            resolution (float, optional): Pulse resolution. Defaults to 1.

        Returns:
            np.ndarray: Height of the envelope for each time step.
        """
        if isinstance(self.waveform, Gaussian):
            sigma = self.waveform.duration / self.waveform.num_sigmas
            mu = self.waveform.duration / 2
            x = np.arange(self.waveform.duration / resolution) * resolution

            return (-1 * self.drag_coefficient * (x - mu) / sigma**2) * self.waveform.envelope()
        raise NotImplementedError(f"Cannot apply drag correction on a {self.waveform.__class__.__name__} waveform.")
