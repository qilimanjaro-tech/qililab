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
