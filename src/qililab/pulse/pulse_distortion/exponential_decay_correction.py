"""Exponential decay correction."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.typings import PulseDistortionName, PulseDistortionSettingsName
from qililab.utils import Factory

from .pulse_distortion import PulseDistortion


@Factory.register
@dataclass(frozen=True, eq=True)
class ExponentialCorrection(PulseDistortion):
    """Exponential decay distortion

    For more info, check SUPLEMENTAL MATERIAL IV. B. in [https://arxiv.org/abs/1907.04818].

    Args:
        tau_bias_tee (float): time constant
        amp (float): amplitude constant
        sampling_rate (float): sampling rate. Defaults to 1.
        norm_factor (float): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (the max height is the furthest number from 0 in the envelope, only checking the real axis/part). Defaults to True.

    Returns:
        PulseDistortion: Distortion to apply to given envelopes in PulseEvent.

    Examples:

        Imagine you want to distort a `Rectangular` envelope with an `ExponentialCorrection`. You could do:

        .. code-block:: python3

            envelope = Rectangular().envelope(duration=..., amplitude=...)
            distorted_envelope = ExponentialCorrection(tau_exponential=1.3, amp=2.0).apply(envelope)

        which would return a distorted envelope with the same real max height as the initial.

        .. note::
            You can find more examples in the docstring of the :class:`PulseDistortion` class.
    """

    name = PulseDistortionName.EXPONENTIAL_CORRECTION
    tau_exponential: float
    amp: float
    sampling_rate: float = 1.0

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (originally created to distort square envelopes).

        Corrects an exponential decay using a linear IIR filter.
        Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

        If `self.auto_norm` is True (default) normalizes the resulting envelope to have the same real max height than the starting one.
        (the max height is the furthest number from 0, only checking the real axis/part)
        If the corrected envelope is zero everywhere or doesn't have a real part this process is skipped.

        Finally it applies the manual `self.norm_factor` to the result, reducing the full envelope by its magnitude.

        (For further details on the normalization implementation see the documentation on PulseDistortion base class)

        Args:
            envelope (numpy.ndarray): array representing the envelope of a pulse for each time step.

        Returns:
            numpy.ndarray: Amplitude of the envelope for each time step.
        """
        if self.amp >= 0.0:
            # Parameters
            alpha = 1 - np.exp(-1 / (self.sampling_rate * self.tau_exponential * (1 + self.amp)))
            k = self.amp / (1 + self.amp - alpha)

            # Coefficients
            a_1 = -(1 - alpha)
            b_0 = 1 - k + k * alpha
            b_1 = -(1 - k) * (1 - alpha)

        else:
            # Parameters
            denominator = 2 * self.tau_exponential * (1 + self.amp) + 1

            # Coefficients
            a_1 = (self.tau_exponential * (1 + 2 * self.amp) - 1) / denominator
            b_0 = (2 * self.tau_exponential + 1) / denominator
            b_1 = (-2 * self.tau_exponential + 1) / denominator

        # Filtered signal
        corr_envelope = signal.lfilter(b=[b_0, b_1], a=[1, a_1], x=envelope)
        return self.normalize_envelope(envelope=envelope, corr_envelope=corr_envelope)

    @classmethod
    def from_dict(cls, dictionary: dict) -> "ExponentialCorrection":
        """Load ExponentialCorrection object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the ExponentialCorrection object.

        Returns:
            ExponentialCorrection: Loaded class.
        """
        local_dictionary = dictionary.copy()
        local_dictionary.pop(RUNCARD.NAME, None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Return dictionary representation of the distortion.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseDistortionSettingsName.TAU_EXPONENTIAL.value: self.tau_exponential,
            PulseDistortionSettingsName.AMP.value: self.amp,
            PulseDistortionSettingsName.SAMPLING_RATE.value: self.sampling_rate,
            PulseDistortionSettingsName.NORM_FACTOR.value: self.norm_factor,
            PulseDistortionSettingsName.AUTO_NORM.value: self.auto_norm,
        }
