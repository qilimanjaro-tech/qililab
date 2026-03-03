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
This module contains all the methods and classes used for automatic calibration.

Examples of how the automatic calibration works, and how the different classes and methods are used
can be found in the :class:`CalibrationController` and :class:`CalibrationNode` classes documentation.

.. currentmodule:: qililab.calibration

CalibrationController Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~CalibrationController

CalibrationNode Class
~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~CalibrationNode

Calibration-related methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~export_nb_outputs
"""

from .calibration_controller import CalibrationController
from .calibration_node import CalibrationNode, export_nb_outputs

__all__ = ["CalibrationController", "CalibrationNode", "export_nb_outputs"]
