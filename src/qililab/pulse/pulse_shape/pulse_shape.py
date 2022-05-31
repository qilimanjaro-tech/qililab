"""PulseShape abstract base class."""
from abc import ABC, abstractmethod

import numpy as np

from qililab.constants import YAML
from qililab.typings import FactoryElement, PulseShapeName


class PulseShape(FactoryElement, ABC):
    """Pulse shape abstract base class."""

    name: PulseShapeName

    @abstractmethod
    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """Compute the amplitudes of the pulse shape envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {YAML.NAME: self.name.value} | self.__dict__

    @abstractmethod
    def __repr__(self):
        """Return string representation of the PulseShape object."""

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Compare PulseShape with another object.

        Args:
            other (object): PulseShape object.
        """
