# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""PulseDistortion abstract base class."""
from abc import abstractmethod
from dataclasses import dataclass

import numpy as np

from qililab.typings.factory_element import FactoryElement
from qililab.utils import Factory


@dataclass(frozen=True, eq=True, kw_only=True)
class PulseDistortion(FactoryElement):
    """Pulse distortions applied to the :class:`PulseShape`'s envelopes, in order to pre-correct our pulses from future lab physical modifications. ``PulseDistortion`` is their abstract base class.

    Every child of this interface needs to contain an `apply` and `to/from_dict` methods (for serialization).


    The `apply` method will apply the distortion correction to the respective passed envelope, and then will call `normalize_envelope` method of this base class.

    Whenever you call a `PulseDistortion` interface child, apart than their respective arguments you can also pass the `norm_factor` & `auto_norm` arguments, to
    modify how such normalization is done.

    If `self.auto_norm` is True (default) normalizes the resulting envelope to have the same real max height than the starting one. (the max height is the furthest number
    from 0, only checking the real axis/part).

    .. code-block:: python3

        if self.auto_norm:
            auto_norm_envelope = corrected_envelope * (original_norm / corrected_norm)

    If the corrected envelope is zero everywhere or doesn't have a real part (`corrected_norm == 0`) this process is skipped, since the factor in the denominator would diverge:

    .. code-block:: python3

        if self.auto_norm:

            if corrected_norm != 0:
                auto_norm_envelope = corrected_envelope * (original_norm / corrected_norm)

            else:
                auto_norm_envelope = corrected_envelope

    And finally, independently of the `auto_norm`, we will then always apply the manual `self.norm_factor` to the result, reducing the full envelope by its magnitude:

    .. code-block:: python3

        final_envelope = almost_final_envelope * self.norm_factor

    Derived: :class:`BiasTeeCorrection`, :class:`ExponentialCorrection` and :class:`LFilterCorrection`

    Args:
        norm_factor (float): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (the max height is the furthest number from 0 in the envelope, only checking the real axis/part). Default to True.

    Examples:

        Imagine you want to distort a `Rectangular` envelope with an `LFilterCorrection`. You could do:

        >>> from qililab.pulse import Rectangular, LFilterCorrection
        >>> envelope = Rectangular().envelope(duration=50, amplitude=1.0)
        >>> distorted_envelope = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6]).apply(envelope)

        which would return a distorted envelope with the same real max height as the initial.

        >>> np.max(distorted_envelope) == np.max(envelope)
        True

        If instead you wanted to manually modify the envelope to make it 90% smaller than the initial, you would instead do:

        >>> distorted_envelope = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], norm_factor=0.9).apply(envelope)
        >>> np.max(distorted_envelope) == 0.9 * np.max(envelope)
        True

        And if you wanted to only apply the scipy correction without any normalization, you would then do:

        >>> distorted_envelope_no_norm = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], auto_norm=False).apply(envelope)
        >>> np.max(distorted_envelope_no_norm) == np.max(envelope)
        False

        Which if ended bigger/smaller than you wanted, you can then also manually modify it like:

        >>> distorted_envelope_manual_norm = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], auto_norm=False, norm_factor=0.8).apply(envelope)
        >>> np.max(distorted_envelope_manual_norm) == 0.8 * np.max(distorted_envelope_no_norm) != np.max(envelope)
        True
    """

    norm_factor: float = 1.0  #: Normalization factor.
    auto_norm: bool = True  #: Auto-normalization flag. Defaults to True.

    @abstractmethod
    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Applies the distortion to the given envelope.

        Args:
            envelope (np.ndarray): Original pulse envelope to be distorted.

        Returns:
            np.ndarray: Distorted pulse envelope.
        """

    @classmethod
    def from_dict(cls, dictionary: dict) -> "PulseDistortion":
        """Loads PulseDistortion object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseDistortion object. It must include the name of the
            correction.

        Returns:
            PulseDistortion: Loaded class.
        """
        distortion_class = Factory.get(name=dictionary["name"])
        return distortion_class.from_dict(dictionary)

    @abstractmethod
    def to_dict(self) -> dict:
        """Returns dictionary of PulseDistortion.

        Returns:
            dict: Dictionary describing the pulse distortion.
        """

    def normalize_envelope(self, envelope: np.ndarray, corr_envelope: np.ndarray) -> np.ndarray:
        """Normalizes the envelope depending on the `norm_factor` and `auto_norm` attributes.

        If `self.auto_norm` is `True` (default) normalizes the resulting envelope to have the same real max height than the starting one.
        (the max height is the furthest number from 0, only checking the real axis/part)
        If the corrected envelope is zero everywhere or doesn't have a real part this process is skipped.

        Finally it applies the manual `self.norm_factor` to the result, reducing the full envelope by its magnitude.

        For further details on the normalization implementation see the docstring of the class.

        Args:
            envelope (np.ndarray): The original envelope before applying the distortion.
            corr_envelope (np.ndarray): The corrected envelope, but that has not yet been normalized.

        Returns:
            np.ndarray: Normalized final envelope.
        """
        # Automatic normalization if applies
        if self.auto_norm:
            norm = np.max(np.abs(np.real(envelope)))
            corr_norm = np.max(np.abs(np.real(corr_envelope)))

            if corr_norm != 0:
                corr_envelope *= norm / corr_norm

        # Apply manual normalization
        return corr_envelope * self.norm_factor
