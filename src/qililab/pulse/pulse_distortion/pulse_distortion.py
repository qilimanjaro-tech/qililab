"""PulseDistortion abstract base class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, eq=True)
class PulseDistortion(ABC):
    """Base class for the pulse distortions."""

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
