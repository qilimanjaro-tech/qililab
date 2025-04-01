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


"""Rectangular pulse shape."""

from dataclasses import dataclass

import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class Cosine(PulseShape):
    r"""Cosine pulse shape like :math:`A/2 (1-\lambda_1\cos(\phi)-\lambda_2\cos(2\phi))`, giving a modified sinusoidal-gaussian.

    - :math:`\lambda_1` cosine :math:`A/2 (1-\cos(x))`: Starts and ends at height 0, with a maximum height A in the middle. Which is a sinusoidal like gaussian:

        .. image:: /classes_images/cos0.png
                :width: 300
                :align: center

    - :math:`\lambda_2` cosine :math:`A/2 (1-\cos(2x))`: Starts and ends at height 0, having two maximums heights A, with a node in between. Which is two sinusoidal like gaussians:

        .. image:: /classes_images/cos1.png
                :width: 300
                :align: center

    The finally function would be a weigthed sum of both ``lambda_1`` and ``lambda_2`` contributions, giving an intermediate modified sinusoidal-gaussian.
    Check the following graph from Wolframalpha, where y is the lambda_2 parameter: [https://imgur.com/a/tjatZsg].

    Examples:
        To get the envelope of a Cosine shape, with ``lambda_2`` equal to ``X``, you need to do:

        .. code-block:: python

            from qililab.pulse.pulse_shape import Cosine

            rectangular_envelope = Cosine(lambda_2=X).envelope(amplitude=1.0, duration=50)

        which for ``X`` being ``0.2`` and ``0.5``, look respectively like:

        .. image:: /classes_images/cosines.png
            :width: 800
            :align: center

    References:
        - Supplement. material B. "Flux pulse parametrization": [https://arxiv.org/abs/1903.02492].
        - OPTIMAL SOLUTION: SMALL CHANGE IN θ: [https://arxiv.org/abs/1402.5467].

    Args:
        lambda_2 (float, optional): Parameter for moving the function :math:`A/2*(1-\cos(x))` into :math:`A/2*(1-\lambda_1\cos(x)-\lambda_2\cos(2x))`
                    which fulfills the constrain: :math:`1=\lambda_1+\lambda_2`. Defaults to 0.
    """

    name = PulseShapeName.COSINE  # noqa: RUF045
    lambda_2: float = 0.0  # between 0 and 1

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """Modified sinusoidal-gaussian envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        x_values = np.linspace(start=0, stop=2 * np.pi, num=int(duration / resolution))
        return amplitude / 2 * (1 - (1 - self.lambda_2) * np.cos(x_values) - self.lambda_2 * np.cos(2 * x_values))
