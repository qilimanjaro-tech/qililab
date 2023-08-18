"""PulseDistortion abstract base class."""
from abc import abstractmethod
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.typings import FactoryElement
from qililab.utils import Factory


@dataclass(frozen=True, eq=True, kw_only=True)
class PulseDistortion(FactoryElement):
    """Base class for the pulse distortions. Every child of this interface needs to contain an `apply` and `to/from_dict` methods (for serialization).

    The `apply` method will apply the distortion correction to the respective passed envelope, and then will call `normalize_envelope` method of this base class.

    Whenever you call a `PulseDistortion` interface child, apart than their respective arguments you can also pass the `norm_factor` & `auto_norm` arguments, to
    modify how such normalization is done. Basically:

    If `self.auto_norm` is True (default) normalizes the resulting envelope to have the same real max height than the starting one. (the max height is the furthest number
    from 0, only checking the real axis/part). If the corrected envelope is zero everywhere or doesn't have a real part this process is skipped, since the factor would diverge:
    .. code-block:: python3
        if self.auto_norm:
            original_norm = np.max(np.abs(np.real(original_envelope)))
            corrected_norm = np.max(np.abs(np.real(corrected_envelope)))

            auto_norm_envelope = corrected_envelope * (original_norm / corrected_norm) if corrected_norm != 0 else corrected_envelope

    And independently of the `auto_norm`, we will then always apply the manual `self.norm_factor` to the result, reducing the full envelope by its magnitude:
    .. code-block:: python3
        final_envelope = envelope * self.norm_factor

    Args:
        norm_factor (float): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (the max height is the furthest number from 0 in the envelope, only checking the real axis/part). Default to True.

    Examples:

        Imagine you want to distort a `Rectangular` envelope with an `LFilterCorrection`. You could do:

        .. code-block:: python3

            envelope = Rectangular().envelope(duration=..., amplitude=...)
            distorted_envelope = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6]).apply(envelope)

        which would return a distorted envelope with the same real max height as the initial.

        If instead you wanted to manually modify the envelope to make it 90% smaller than the initial, you would instead do:

        .. code-block:: python3

            distorted_envelope = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], norm_factor=0.9).apply(envelope)

        And if you wanted to only apply the scipy correction without any normalization, you would then do:

        .. code-block:: python3

            distorted_envelope = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], auto_norm=False).apply(envelope)

        Which if ended bigger/smaller than you wanted, you can then also manually modify it like:

        .. code-block:: python3

            distorted_envelope = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], auto_norm=False, norm_factor=0.8).apply(envelope)
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
        """Normalizes the envelope depending on the `norm_factor` and `auto_norm` attributes.

        If `self.auto_norm` is `True` (default) normalizes the resulting envelope to have the same real max height than the starting one.
        (the max height is the furthest number from 0, only checking the real axis/part)
        If the corrected envelope is zero everywhere or doesn't have a real part this process is skipped.

        Finally it applies the manual `self.norm_factor` to the result, reducing the full envelope by its magnitude.

        (For further details on the normalization implementation see the documentation of the class)

        Args:
            envelope (np.ndarray): The original envelope before applying the distortion.
            corr_envelope (np.ndarray): The corrected envelope, but that has not yet been normalized.

        Returns:
            np.ndarray: Normalized final envelope.
        """
        # Automatic and manual normalization
        if self.auto_norm:
            norm = np.max(np.abs(np.real(envelope)))
            corr_norm = np.max(np.abs(np.real(corr_envelope)))

            return (
                corr_envelope * self.norm_factor * (norm / corr_norm)
                if corr_norm != 0
                else corr_envelope * self.norm_factor
            )

        # Only manual normalization
        return corr_envelope * self.norm_factor
