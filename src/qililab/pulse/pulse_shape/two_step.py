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

"""Two-Step pulse shape."""

from dataclasses import dataclass

import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class TwoStep(PulseShape):
    """Two step pulse shape. Given by two concatenated square pulses.

    Examples:
        To get the envelope of a two-step shape, with ``amplitude`` equal to ``X``, you need to do:

        .. code-block:: python

            from qililab.pulse.pulse_shape import TwoStep

            two_step_envelope = TwoStep().envelope(amplitude=X, duration=50)
    """

    name = PulseShapeName.TWOSTEP  # noqa: RUF045
    step_amplitude: float
    step_duration: int

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """Two step envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        step_duration = self.step_duration
        step_amp = self.step_amplitude
        return np.concatenate((amplitude * np.ones(step_duration), step_amp * np.ones(duration - step_duration)))
