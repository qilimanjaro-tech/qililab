"""Bias tee correction."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.typings import PulseDistortionName
from qililab.utils import Factory

from .pulse_distortion import PulseDistortion


@Factory.register
@dataclass(frozen=True, eq=True)
class BiasTeeCorrection(PulseDistortion):
    """Bias tee distortion.

    For more info, check SUPLEMENTAL MATERIAL in [https://arxiv.org/abs/1907.04818].

    Args:
        tau_bias_tee (float): Time constant.
        sampling_rate (float): Sampling rate. Defaults to 1.
        norm_factor (float): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (The max height is the furthest number from 0 in the envelope, only checking the real axis/part). Defaults to True.

    Returns:
        PulseDistortion: Distortion to apply to given envelopes in PulseEvent.

    Examples:

        Imagine you want to distort a `Rectangular` envelope with a `BiasTeeCorrection`. You could do:

        .. code-block:: python3

            envelope = Rectangular().envelope(duration=..., amplitude=...)
            distorted_envelope = BiasTeeCorrection(tau_bias_tee=1.3).apply(envelope)

        which would return a distorted envelope with the same real max height as the initial.

        .. note::
            You can find more examples in the docstring of the :class:`PulseDistortion` class.
    """

    name = PulseDistortionName.BIAS_TEE_CORRECTION
    tau_bias_tee: float
    sampling_rate: float = 1.0

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (originally created to distort square envelopes).

        Corrects for a bias tee using a linear IIR filter with time constant tau.

        If `self.auto_norm` is True (default) normalizes the resulting envelope to have the same real max height than the starting one.
        (the max height is the furthest number from 0, only checking the real axis/part)
        If the corrected envelope is zero everywhere or doesn't have a real part this process is skipped.

        Finally it applies the manual `self.norm_factor` to the result, reducing the full envelope by its magnitude.

        For further details on the normalization implementation see the docstring on :class:`PulseDistortion` base class.

        Args:
            envelope (numpy.ndarray): array representing the envelope of a pulse for each time step.

        Returns:
            numpy.ndarray: Amplitude of the envelope for each time step.
        """
        # Parameters
        k = 2 * self.tau_bias_tee * self.sampling_rate

        # Coefficients
        a = [1, -1]
        b = [(k + 1) / k, -(k - 1) / k]

        # Filtered signal
        corr_envelope = signal.lfilter(b=b, a=a, x=envelope)
        return self.normalize_envelope(envelope=envelope, corr_envelope=corr_envelope)

    @classmethod
    def from_dict(cls, dictionary: dict) -> "BiasTeeCorrection":
        """Load BiasTeeCorrection object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the BiasTeeCorrection object.

        Returns:
            BiasTeeCorrection: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Return dictionary representation of the distortion.

        Returns:
            dict: Dictionary.
        """
        return {
            "name": self.name.value,
            "tau_bias_tee": self.tau_bias_tee,
            "sampling_rate": self.sampling_rate,
            "norm_factor": self.norm_factor,
            "auto_norm": self.auto_norm,
        }
