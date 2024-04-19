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
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
from scipy.special import erf

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class FlatTop(PulseShape):
    """Rectangular/square pulse shape. Given by a constant height line.

    Examples:
        To get the envelope of a rectangular shape, with ``amplitude`` equal to ``X``, you need to do:

        .. code-block:: python

            from qililab.pulse.pulse_shape import Rectangular
            rectangular_envelope = Rectangular().envelope(amplitude=X, duration=50)

        which for ``X`` being ``1.`` and ``0.75``, look respectively like:

        .. image:: /classes_images/rectangulars.png
            :width: 800
            :align: center
    """

    name = PulseShapeName.FLATTOP  #: Name of the rectangular pulse shape.
    gaussian: float

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0, buffer: float = 3.0) -> np.ndarray:
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        x = np.arange(0, duration, resolution)
        A = amplitude
        g = self.gaussian
        buf = buffer
        dur = duration
        return 0.5 * A * np.real((erf(g * x - buf) - erf(g * (x - (dur + -buf / g)))))

    @classmethod
    def from_dict(cls, dictionary: dict) -> "FlatTop":
        """Loads Rectangular object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Rectangular object/shape including the name of the pulse shape.

        Returns:
            Rectangular: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the Rectangular object/shape.

        Returns:
            dict: Dictionary representation of the pulse shape including its name.
        """
        return {"name": self.name.value, "gaussian": self.gaussian}
