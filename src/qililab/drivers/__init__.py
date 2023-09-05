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
This module contains the qcodes drivers supported by qililab, together with the interfaces for each
type of driver.

.. currentmodule:: qililab.drivers

Drivers
~~~~~~~

QBlox
======

.. autosummary::
    :toctree: api

    ~Cluster
    ~Pulsar
    ~SpiRack

Rohde & Schwarz
===============

.. autosummary::
    :toctree: api

    ~RhodeSchwarzSGS100A

Keithley
========

.. autosummary::
    :toctree: api

    ~Keithley2600

Yokogawa
========

.. autosummary::
    :toctree: api

    ~GS200

Interfaces
~~~~~~~~~~

.. currentmodule:: qililab.drivers.interfaces

.. autosummary::
    :toctree: api

    ~AWG
    ~Digitiser
    ~LocalOscillator
    ~CurrentSource
    ~VoltageSource
    ~Attenuator
"""
from .instruments import GS200, Cluster, ERASynthPlus, Keithley2600, Pulsar, RhodeSchwarzSGS100A, SpiRack
