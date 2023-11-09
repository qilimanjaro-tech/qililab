"""
This module contains all the methods and classes used for automatic calibration.

A high level view of how the automatic calibration algorithm works and how the different classes and methods are used
can be read from: https://arxiv.org/abs/1803.03226

**Examples** are found in the `qililab/examples/calibration` folder

.. currentmodule:: qililab.calibration

CalibrationController class
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
