"""PulseDistortion abstract base class."""
from abc import abstractmethod
from dataclasses import dataclass, field

import numpy as np

from qililab.typings import FactoryElement, PulseDistortionName


@dataclass(frozen=True, eq=True)
class PulseDistortion(FactoryElement):
    """Base class for the pulse distortions."""

    name: PulseDistortionName = field(init=False)

    @abstractmethod
    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """_summary_

        Args:
            envelope (np.ndarray): Original pulse envelope to be distorted.

        Returns:
            np.ndarray: Distorted pulse envelope.
        """

    @classmethod
    @abstractmethod
    def from_dict(cls, dictionary: dict) -> "PulseDistortion":
        """Load PulseDistortion object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseDistortion object.

        Returns:
            PulseDistortion: Loaded class.
        """

    @abstractmethod
    def to_dict(self) -> dict:
        """Return dictionary of PulseDistortion.

        Returns:
            dict: Dictionary describing the pulse distortion.
        """
