"""This module contains the waveforms that can be played within a QProgram.

.. currentmodule:: qililab

Waveforms
~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Waveform
    ~Arbitrary
    ~Gaussian
    ~DragWaveform
    ~Square
    ~IQPair
"""

from .arbitrary import Arbitrary
from .drag import Drag as DragWaveform
from .gaussian import Gaussian
from .iq_pair import IQPair
from .square import Square
from .waveform import Waveform
