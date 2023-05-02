"""PulseDistortion abstract base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

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

    # TODO: Implement from_dict method.
    @classmethod
    def from_dict(cls, dictionary: dict) -> PulseDistortion:
        """Load PulseDistortion object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseDistortion object.

        Returns:
            PulseDistortion: Loaded class.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """Return dictionary of PulseDistortion.

        Returns:
            dict: Dictionary describing the pulse distortion.
        """
        dictionary = self.__dict__.copy()
        for key, value in dictionary.items():
            if isinstance(value, Enum):
                dictionary[key] = value.value
        return dictionary
