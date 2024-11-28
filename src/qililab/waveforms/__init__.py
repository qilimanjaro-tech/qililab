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

"""This module contains the waveforms that can be played within a QProgram.

.. currentmodule:: qililab

Waveforms
~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Waveform
    ~Square
    ~Ramp
    ~Gaussian
    ~Arbitrary
    ~DragCorrection
    ~Chained
    ~IQPair
    ~FlatTop
"""

from .arbitrary import Arbitrary
from .chained import Chained
from .flat_top import FlatTop
from .gaussian import Gaussian
from .gaussian_drag_correction import GaussianDragCorrection
from .iq_drag import IQDrag
from .iq_pair import IQPair
from .ramp import Ramp
from .square import Square
from .waveform import Waveform

__all__ = [
    "Arbitrary",
    "Chained",
    "FlatTop",
    "Gaussian",
    "GaussianDragCorrection",
    "IQDrag",
    "IQPair",
    "Ramp",
    "Square",
    "Waveform",
]
