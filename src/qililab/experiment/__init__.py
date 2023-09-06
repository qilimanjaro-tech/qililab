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
This module contains the Experiment class, which is used to execute circuits in hardware.

.. currentmodule:: qililab

Experiment Class
~~~~~~~~~~~~~~~~


.. autosummary::
    :toctree: api

    ~Experiment

.. currentmodule:: qililab.experiment

Experiment Portfolio
~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~ExperimentAnalysis
    ~Rabi
    ~T1
    ~FlippingSequence
    ~T2Echo
"""
from .experiment import Experiment
from .portfolio import T1, ExperimentAnalysis, FlippingSequence, Rabi, T2Echo
