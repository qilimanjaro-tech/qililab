"""PulseShape abstract base class."""
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from qililab.constants import RUNCARD
from qililab.typings import FactoryElement, PulseShapeName


@dataclass(unsafe_hash=True, eq=True)
class PulseShape(FactoryElement):
    """Pulse shape abstract base class."""

    name: PulseShapeName = field(init=False)

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """Compute the amplitudes of the pulse shape envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        raise NotImplementedError

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        dictionary = self.__dict__.copy()
        for key, value in dictionary.items():
            if isinstance(value, Enum):
                dictionary[key] = value.value
        return dictionary
