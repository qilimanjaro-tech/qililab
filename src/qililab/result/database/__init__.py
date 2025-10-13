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

"""This module contains the classes used to return the results of the execution of a program.

.. currentmodule:: qililab.result

Classes
~~~~~~~~

.. autosummary::
    :toctree: api

    experiment_results.ExperimentResults
    Result
    MeasurementResult
    QbloxMeasurementResult


Functions
~~~~~~~~~~

.. autosummary::
    :toctree: api

    load_results
    save_results

"""
from .database_autocal import Autocal_Measurement, Calibration_run
from .database_manager import DatabaseManager, get_db_manager, load_by_id
from .database_measurements import Cooldown, Sample, Measurement
from .database_qaas import QaaS_Experiment


__all__ = [
    "Autocal_Measurement",
    "Calibration_run",
    "Cooldown",
    "DatabaseManager",
    "Measurement",
    "QaaS_Experiment",
    "Sample",
    "get_db_manager",
    "load_by_id",
]
