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

"""Drag pulse shape."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


# pylint: disable=anomalous-backslash-in-string
@Factory.register
@dataclass(frozen=True, eq=True)
class Depletion(PulseShape):
    """TODO: write docs"""

    name = PulseShapeName.DEPLETION  #: Name of the drag pulse shape.

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """TODO: add docs

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        return (1 + 1j) * amplitude * np.ones(round(duration / resolution))

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Depletion":
        """Loads Depletion object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Depletion pulse

        Returns:
            Depletion: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the Drag object/shape.

        Returns:
            dict: Dictionary representing the Drag pulse shape. It contains the name of the pulse shape, the number of sigmas and
            the drag coefficient.
        """
        return {
            "name": self.name.value,
        }
