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

"""Gaussian pulse shape."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


# pylint: disable=anomalous-backslash-in-string
@Factory.register
@dataclass(frozen=True, eq=True)
class Gaussian(PulseShape):
    """Standard centered Gaussian pulse shape, symmetrically spanning for ``num_sigmas`` over the pulse duration.

    The normal distribution's parameters :math:`\mu` (mean) and :math:`\sigma` (standard deviation) will be therefore
    defined by :math:`\mu =` ``duration`` :math:`/ 2` and :math:`\sigma =` ``duration`` :math:`/` ``num_sigmas``:

    .. math::

        Gaussian(x) = A * exp(-0.5 * (x - \mu)^2 / \sigma^2)

    You can think of it, as if an infinite expanding gaussian, is symmetrically cut in the given ``num_sigmas``, then that cut is
    expanded to occupy all the pulse duration, and then is shifted down so that it starts at 0.

    Examples:

        To get the envelope of a gaussian, with ``num_sigmas`` equal to ``X``, you need to do:

        .. code-block:: python

            from qililab.pulse.pulse_shape import Gaussian
            gaussian_envelope = Gaussian(num_sigmas=X).envelope(duration=50, amplitude=1)

        which for ``X`` being ``1``, ``4``, ``6`` or ``8``, look respectively like:

        .. image:: /classes_images/gaussians.png
            :width: 800
            :align: center

        This comes from the following steps, parting from a "full" gaussian (big ``num_sigma``) [blue]:
            1. you cut a full gaussian to the given ``num_sigmas``, for example ``1`` [small purple].
            2. in reality this cut gaussian, actually extends all the duration [big purple],
            3. you shift/distortion down the cut gaussian, so it starts at 0 height [red].

        .. image:: /classes_images/gaussian_explanation.png
            :width: 400
            :align: center

    Args:
        num_sigmas (float): Sigma number of the gaussian pulse shape. Defines the width of the gaussian pulse.
    """

    name = PulseShapeName.GAUSSIAN  #: Name of the gaussian pulse shape.
    num_sigmas: float  #: Sigma number of the gaussian pulse shape.

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """Gaussian envelope centered with respect to the pulse.

        The gaussian is symmetrically cut in the given ``num_sigmas``, meaning that it starts and ends at that sigma width.

        And then to avoid introducing noise at time 0, the full gaussian is shifted down so that it starts at 0.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        sigma = duration / self.num_sigmas
        time = np.arange(duration / resolution) * resolution
        mu_ = duration / 2

        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / sigma**2)
        norm = np.amax(np.abs(np.real(gaussian)))

        gaussian = gaussian - gaussian[0]  # Shift to avoid introducing noise at time 0
        corr_norm = np.amax(np.abs(np.real(gaussian)))

        return gaussian * norm / corr_norm if corr_norm != 0 else gaussian

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Gaussian":
        """Loads Gaussian object/shape from dictionary.

        The dictionary representation must include the name of the pulse shape and the number of sigmas.

        Args:
            dictionary (dict): Dictionary representation of the Gaussian object/shape including the name of the pulse shape and
            the number of sigmas.

        Returns:
            Gaussian: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the Gaussian object/shape.

        Returns:
            dict: Dictionary representation including the name of the pulse shape and the number of sigmas.
        """
        return {
            "name": self.name.value,
            "num_sigmas": self.num_sigmas,
        }
