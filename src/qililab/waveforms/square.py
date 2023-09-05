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


class Square(Waveform):  # pylint: disable=too-few-public-methods
    """Square (rectangular) waveform"""

    def __init__(self, amplitude: float, duration: int):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
        """
        self.amplitude = amplitude
        self.duration = duration

    def envelope(self, resolution: float = 1):
        """Returns the pulse matrix

        Args:
            resolution (int, optional): Pulse resolution. Defaults to 1.

        Returns:
            np.ndarray: pulse matrix
        """
        return self.amplitude * np.ones(round(self.duration / resolution))
