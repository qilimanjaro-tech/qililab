"""This module contains the QProgram result classes and all the needed components to retrieve and handle measurement results.

.. currentmodule:: qililab.result.qprogram

QProgram Results
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    MeasurementResult
    QProgramResults

Qblox Measurement Results
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    QbloxMeasurementResult

QuantumMachines Measurement Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    QuantumMachinesMeasurementResult
"""

from .measurement_result import MeasurementResult
from .qblox_measurement_result import QbloxMeasurementResult
from .qprogram_results import QProgramResults
from .quantum_machines_measurement_result import QuantumMachinesMeasurementResult

__all__ = [
    "MeasurementResult",
    "QProgramResults",
    "QbloxMeasurementResult",
    "QuantumMachinesMeasurementResult",
]
