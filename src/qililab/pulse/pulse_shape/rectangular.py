"""Rectangular pulse shape."""
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class Rectangular(PulseShape):
    """Rectangular/square pulse shape."""

    name: PulseShapeName = PulseShapeName.RECTANGULAR

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        return amplitude * np.ones(round(duration / resolution))

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Rectangular":
        """Load Rectangular object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Rectangular object/shape.

        Returns:
            Rectangular: Loaded class.
        """
        return cls()

    def to_dict(self):
        """Return dictionary representation of the Rectangular object/shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
        }
