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

from .measurement_result import MeasurementResult
from .qblox_measurement_result import QbloxMeasurementResult
from .qprogram_results import QProgramResults
from .quantum_machines_measurement_result import QuantumMachinesMeasurementResult

"""This module contains the QProgram result class and all the needed information to get the results information.

.. currentmodule:: qililab

QProgram Results
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~MeasurementResults
    ~QProgramResults

Qblox Measurements Results
~~~~~~~~~

.. autosummary::
    :toctree: api

    ~QbloxCompiler

QuantumMachines Measurements Results
~~~~~~~~~

.. autosummary::
    :toctree: api

    ~QuantumMachinesMeasurementResult

"""

__all__ = ["MeasurementResult", "QProgramResults", "QbloxMeasurementResult", "QuantumMachinesMeasurementResult"]
