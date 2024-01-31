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

"""
This module contains all the methods and classes used to define a pulse sequence.

.. currentmodule:: qililab.pulse

Pulse Schedules
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~PulseSchedule
    ~PulseBusSchedule
    ~PulseEvent

Pulses
~~~~~~

.. autosummary::
    :toctree: api

    ~Pulse

Pulse Shapes
=============

.. autosummary::
    :toctree: api

    ~PulseShape
    ~Gaussian
    ~Drag
    ~Rectangular
    ~SNZ
    ~Cosine

Distortions
~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~PulseDistortion
    ~LFilterCorrection
    ~BiasTeeCorrection
    ~ExponentialCorrection
"""
from .pulse import Pulse
from .pulse_bus_schedule import PulseBusSchedule
from .pulse_distortion import BiasTeeCorrection, ExponentialCorrection, LFilterCorrection, PulseDistortion
from .pulse_event import PulseEvent
from .pulse_schedule import PulseSchedule
from .pulse_shape import SNZ, Cosine, Drag, FlatTop, Gaussian, PulseShape, Rectangular
from .qblox_compiler import QbloxCompiler
