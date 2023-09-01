"""
This module contains all the methods and classes used for automatic calibration.
A high level view of how the automatic calibration algorithm works and how the different classes and methods are used 
can be found in this Notion page: https://www.notion.so/qilimanjaro/Automatic-qubit-calibration-algorithm-architecture-73133434c9c04b9cb8f6bd178d0b06d9?pvs=4

Examples are found in the `qililab/src/qililab/automatic_calibration/examples` folder

Things left to do to improve this module:

    - Task 1
    - Task 2

.. currentmodule:: qililab.automatic_calibration

Calibration-related methods
~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~visualize_calibration_graph
    ~get_timestamp
    ~is_timeout_expired
    ~get_random_values
    ~get_raw_data 
    ~get_iq_from_raw
    ~plot_iq
    ~plot_fit
    ~get_most_recent_folder
    
Controller class
~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Controller


CalibrationNode Class
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~CalibrationNode

"""

from .calibration_node import CalibrationNode
from .controller import Controller
from .calibration_utils.calibration_utils import get_timestamp, is_timeout_expired, get_random_values, get_raw_data, get_iq_from_raw, plot_iq, plot_fit, get_timestamp, get_random_values, get_most_recent_folder, visualize_calibration_graph