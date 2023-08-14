"""This module contains the waveforms that can be played within a QProgram.

.. currentmodule:: qililab

Waveforms
~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Waveform
    ~Arbitrary
    ~Gaussian
    ~DragPair
    ~Square
    ~IQPair
"""

from .arbitrary import Arbitrary
from .drag import Drag as DragPair
from .gaussian import Gaussian
from .iq_pair import IQPair
from .square import Square
from .waveform import Waveform
