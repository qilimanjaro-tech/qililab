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

from qililab.qprogram.decorators import requires_domain
from qililab.qprogram.variable import Domain

from .waveform import Waveform


class Square(Waveform):  # pylint: disable=too-few-public-methods
    """Square (rectangular) waveform. Given by a constant height line.

    Args:
        duration (int): Duration of the pulse (ns).
        amplitude (float): Maximum amplitude of the pulse.

    Examples:
        To get the envelope of a square waveform, with ``amplitude`` equal to ``X``, you need to do:

        .. code-block:: python

            import qililab as ql
            square_envelope = ql.Square( amplitude=X, duration=50).envelope()

        which for ``X`` being ``1.`` and ``0.75``, look respectively like:

        .. image:: /classes_images/rectangulars.png
            :width: 800
            :align: center
    """

    @requires_domain("amplitude", Domain.Voltage)
    @requires_domain("duration", Domain.Time)
    def __init__(self, amplitude: float, duration: int):
        super().__init__()
        self.amplitude = amplitude
        self.duration = duration

    def envelope(self, resolution: int = 1) -> np.ndarray:
        """Constant amplitude envelope.

        Args:
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            np.ndarray: Height of the envelope for each time step.
        """
        return self.amplitude * np.ones(round(self.duration / resolution))

    def get_duration(self) -> int:
        """Get the duration of the waveform.

        Returns:
            int: The duration of the waveform in ns.
        """
        return self.duration
