"""PulseShape abstract base class."""
from abc import abstractmethod
from dataclasses import dataclass, field

import numpy as np

from qililab.typings import PulseShapeName
from qililab.typings.factory_element import FactoryElement
from qililab.utils import Factory


@dataclass(frozen=True, eq=True)
class PulseShape(FactoryElement):
    """Pulse shape abstract base class."""

    name: PulseShapeName = field(init=False)

    @abstractmethod
    def envelope(self, duration: int, amplitude: float, resolution: float) -> np.ndarray:
        """Compute the amplitudes of the pulse shape envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

    @classmethod
    def from_dict(cls, dictionary: dict) -> "PulseShape":
        """Return dictionary representation of the pulse shape.

        Args:
            dictionary (dict): Dictionary representation of the PulseShape object.

        Returns:
            PulseShape: Loaded class.
        """
        shape_class = Factory.get(name=dictionary["name"])
        return shape_class.from_dict(dictionary)

    @abstractmethod
    def to_dict(self) -> dict:
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
