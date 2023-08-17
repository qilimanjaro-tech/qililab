"""PulseDistortion abstract base class."""
from abc import abstractmethod
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.typings import FactoryElement
from qililab.utils import Factory


@dataclass(frozen=True, eq=True, kw_only=True)
class PulseDistortion(FactoryElement):
    """Base class for the pulse distortions.

    Whenever you call a PulseDistortion child, appart than their arguments you can also pass the
    norm_factor & auto_norm arguments, to modify the normalization of the .apply method.

    Args:
        norm_factor (float): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (the max height is the furthest number from 0 in the envelope, only checking the real axis/part). Default to True.
    """

    norm_factor: float = 1.0
    auto_norm: bool = True

    @abstractmethod
    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """_summary_

        Args:
            envelope (np.ndarray): Original pulse envelope to be distorted.

        Returns:
            np.ndarray: Distorted pulse envelope.
        """

    @classmethod
    def from_dict(cls, dictionary: dict) -> "PulseDistortion":
        """Load PulseDistortion object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseDistortion object.

        Returns:
            PulseDistortion: Loaded class.
        """
        distortion_class = Factory.get(name=dictionary[RUNCARD.NAME])
        return distortion_class.from_dict(dictionary)

    @abstractmethod
    def to_dict(self) -> dict:
        """Return dictionary of PulseDistortion.

        Returns:
            dict: Dictionary describing the pulse distortion.
        """

    def normalize_envelope(self, envelope: np.ndarray, corr_envelope: np.ndarray) -> np.ndarray:
        """Normalizes the envelope depending on the norm_factor and auto_norm attributes.

        If self.auto_norm is True (default) normalizes the resulting envelope to have the same max height than the starting one.
        (the max height is the furthest number from 0, only checking the real axis/part)

        Finally it applies the manual self.norm_factor to the result, reducing the full envelope by its magnitude
        """
        # Automatic and manual normalization
        if self.auto_norm:
            norm = np.max(np.abs(np.real(envelope)))
            corr_norm = np.max(np.abs(np.real(corr_envelope)))
            return corr_envelope * self.norm_factor * (norm / corr_norm)

        # Only manual normalization
        return corr_envelope * self.norm_factor
