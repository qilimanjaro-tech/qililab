"""PulseShape abstract base class."""
from dataclasses import dataclass, field

import numpy as np

from qililab.constants import RUNCARD
from qililab.typings import FactoryElement, PulseShapeName


@dataclass(frozen=True, eq=True)
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
        return self.__dict__
