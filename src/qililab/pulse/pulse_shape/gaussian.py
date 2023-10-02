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


@Factory.register
@dataclass(frozen=True, eq=True)
class Gaussian(PulseShape):
    """Standard Gaussian pulse shape:

    .. math::

        Gaussian(x) = amplitude * exp(-0.5 * (x - mu)^2 / sigma^2)

    Args:
        num_sigmas (float): Sigma number of the gaussian pulse shape. Defines the height of the gaussian pulse.
    """

    name = PulseShapeName.GAUSSIAN  #: Name of the gaussian pulse shape.
    num_sigmas: float  #: Sigma number of the gaussian pulse shape.

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Gaussian envelope centered with respect to the pulse.

        The first point of the gaussian in the envelope is shifted to avoid introducing noise at time 0.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

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

    def to_dict(self):
        """Returns dictionary representation of the Gaussian object/shape.

        Returns:
            dict: Dictionary representation including the name of the pulse shape and the number of sigmas.
        """
        return {
            "name": self.name.value,
            "num_sigmas": self.num_sigmas,
        }
