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


# isort: skip_file
from .experiment_live_plot import ExperimentLivePlot
from .experiment_results import ExperimentResults
from .result import Result
from .result_management import load_results, save_results

# Moving database here to avoid circular imports
from .database import (
    AutocalMeasurement,
    CalibrationRun,
    Cooldown,
    DatabaseManager,
    QaaS_Experiment,
    Measurement,
    Sample,
    get_db_manager,
    load_by_id,
)
from .stream_results import StreamArray, stream_results
from .qprogram import MeasurementResult, QbloxMeasurementResult

__all__ = [
    "AutocalMeasurement",
    "CalibrationRun",
    "Cooldown",
    "DatabaseManager",
    "ExperimentLivePlot",
    "ExperimentResults",
    "Measurement",
    "MeasurementResult",
    "QaaS_Experiment",
    "QbloxMeasurementResult",
    "Result",
    "Sample",
    "StreamArray",
    "get_db_manager",
    "load_by_id",
    "load_results",
    "save_results",
    "stream_results",
]
