"""
This module contains all the methods and classes used to define a Platform, which is a representation
of a laboratory.

Platform Class
~~~~~~~~~~~~~~~~

.. currentmodule:: qililab.platform

.. autosummary::
    :toctree: api

    ~Platform


Platform Components
~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Bus
"""
from .components import Bus, BusElement, Buses
from .platform import Platform
