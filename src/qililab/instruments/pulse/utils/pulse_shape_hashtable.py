"""Class used as hashtable to load the class corresponding to a given category"""
from typing import Type

from qililab.instruments.pulse.pulse_shape.drag import Drag
from qililab.instruments.pulse.pulse_shape.gaussian import Gaussian
from qililab.instruments.pulse.pulse_shape.rectangular import Rectangular


class PulseShapeHashTable:
    """Hash table that loads a specific class given an object's name."""

    gaussian = Gaussian
    rectangular = Rectangular
    drag = Drag

    @classmethod
    def get(cls, name: str) -> Type[Gaussian | Rectangular | Drag]:
        """Return class attribute."""
        return getattr(cls, name)
