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
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Type, TypeVar

import numpy as np

from qililab.typings import PulseShapeName
from qililab.typings.factory_element import FactoryElement
from qililab.utils import Factory

T = TypeVar("T", bound="PulseShape")


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
    def from_dict(cls: Type[T], dictionary: dict) -> T:
        """Loads a `PulseShape` object from a dictionary representation.

        Args:
            dictionary (dict): Dictionary representation of the `PulseShape` object, containing all its attributes.
                If called directly from the Abstract parent class: `PulseShape`, it must include the child class name to instantiate.

        Returns:
            PulseShape: PulseShape loaded class, including the name of the pulse shape and its attributes set.
        """
        # For calls from parent PulseShape:
        if cls is PulseShape:
            shape_class = Factory.get(name=dictionary["name"])
            return shape_class.from_dict(dictionary)

        # For calls from childs directly:
        local_dictionary = deepcopy(dictionary)
        name = local_dictionary.pop("name", None)
        # If the dict name is not the same as the class name, raise an error:
        if name not in [cls.name.value, None]:
            raise ValueError(f"Class: {cls.name.value} to instantiate, does not match the given dict name {name}")
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the `PulseShape`. This includes the class name an all its attributes.

        Returns:
            dict: Dictionary describing the `PulseShape`, including the name and its attributes.
        """
        return {"name": self.name.value} | {
            attribute: getattr(self, attribute) for attribute in self.__dataclass_fields__.keys()
        }
