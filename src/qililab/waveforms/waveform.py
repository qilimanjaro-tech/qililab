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

"""Waveform protocol class."""
from abc import abstractmethod
from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Waveform(Protocol):  # pylint: disable=too-few-public-methods, disable=missing-class-docstring
    """Waveforms describes the pulses envelope's shapes. ``Waveform`` is their abstract base class.

    Every child of this interface needs to contain an `envelope` method.

    The `envelope` method will create the corresponding array of each shape.

    Derived: :class:`Arbitrary`,  :class:`Square`, :class:`Gaussian` and :class:`DragCorrection`.
    """

    @abstractmethod
    def envelope(self) -> np.ndarray:
        """Returns the pulse height for each time step.

        Returns:
            np.ndarray: Height of the envelope for each time step.
        """
