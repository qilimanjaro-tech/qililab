"""Rectangular pulse shape."""
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class Cosine(PulseShape):
    """Cosine pulse shape."""

    name = PulseShapeName.COSINE

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Cosine envelope that goes like A/2*(1-cos(x)), giving a sinusoidal-gaussian.

        Starts at height 0 (phase=0), maximum height A (phase=pi) and ends at height 0 (phase=2pi)

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        x_values = np.linspace(start=0, stop=2 * np.pi, num=int(duration / resolution))

        return amplitude / 2 * (1 - np.cos(x_values))

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Cosine":
        """Load Cosine object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Cosine object/shape.

        Returns:
            Cosine: Loaded class.
        """
        local_dictionary = dictionary.copy()
        local_dictionary.pop(RUNCARD.NAME, None)
        return cls(**local_dictionary)

    def to_dict(self):
        """Return dictionary representation of the Cosine object/shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
        }
