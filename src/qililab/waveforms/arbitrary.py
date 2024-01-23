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

"""Arbitrary waveform."""
import numpy as np

from .waveform import Waveform


class Arbitrary(Waveform):  # pylint: disable=too-few-public-methods, disable=missing-class-docstring
    """Arbitrary waveform. Creates a waveform with the passed envelope.

    Args:
        samples(np.ndarray): Passed envelope to base the waveform on.

    Examples:
        If you want to create a waveform with an envelope given by:

        .. code-block:: python

            import numpy as np
            samples = np.ones(50)

        You would just need to do:

        .. code-block:: python

            import qililab as ql
            arbitrary_envelope = ql.Arbitrary(samples=samples)
    """

    def __init__(self, samples: np.ndarray):
        super().__init__()
        self.samples = samples

    def envelope(self, resolution: int = 1) -> np.ndarray:
        """Returns the envelope corresponding to the arbitrary waveform.

        Args:
            resolution (int, optional): Pulse resolution. Defaults to 1.

        Returns:
            np.ndarray: Height of the envelope for each time step.
        """
        if resolution == 1:
            return self.samples

        # Calculate the averaging window
        averaging_window = int(len(self.samples) / resolution)

        # Calculate the moving average
        cumsum = np.cumsum(self.samples)
        cumsum[averaging_window:] = cumsum[averaging_window:] - cumsum[:-averaging_window]
        moving_avg = cumsum[averaging_window:] / averaging_window

        # Apply scaling and shifting
        scale_factor = (self.samples.max() - self.samples.min()) / (moving_avg.max() - moving_avg.min())
        shift = self.samples.max() - moving_avg.max() * scale_factor
        scaled_avg = moving_avg * scale_factor + shift

        # Apply clamping
        clamped_avg = np.clip(scaled_avg, self.samples.min(), self.samples.max())

        return clamped_avg
