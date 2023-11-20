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

"""PulseShape abstract base class."""
from abc import abstractmethod
from dataclasses import dataclass, field

import numpy as np

from qililab.typings import PulseShapeName
from qililab.typings.factory_element import FactoryElement
from qililab.utils import Factory


@dataclass(frozen=True, eq=True)
class PulseShape(FactoryElement):
    """Pulse shapes describe the shape of the :class:`Pulse`'s envelopes. ``PulseShape`` is their abstract base class.

    Every child of this interface needs to contain an `envelope` and `to/from_dict` methods (for serialization).

    The `envelope` method will create the corresponding array of each shape.

    Derived: :class:`Rectangular`, :class:`Gaussian`, :class:`Drag`, :class:`Cosine` and :class:`SNZ`
    """

    name: PulseShapeName = field(init=False)  #: Name of the pulse shape.

    @abstractmethod
    def envelope(self, duration: int, amplitude: float, resolution: float) -> np.ndarray:
        """Computes the amplitudes of the pulse shape envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            resolution (float): Resolution of the pulse envelope.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

    @classmethod
    def from_dict(cls, dictionary: dict) -> "PulseShape":
        """Returns dictionary representation of the pulse shape.

        Args:
            dictionary (dict): Dictionary representation of the PulseShape object.

        Returns:
            PulseShape: PulseShape loaded class, including the name of the pulse shape and attributes.
        """
        shape_class = Factory.get(name=dictionary["name"])
        return shape_class.from_dict(dictionary)

    @abstractmethod
    def to_dict(self) -> dict:
        """Returns dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary representation of the pulse shape including the name and attributes of the pulse shape.
        """
