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

"""Exponential decay correction."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.typings import PulseDistortionName
from qililab.utils import Factory

from .pulse_distortion import PulseDistortion


@Factory.register
@dataclass(frozen=True, eq=True)
class ExponentialCorrection(PulseDistortion):
    """Exponential decay distortion. Corrects an exponential decay using a linear IIR filter.

    Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

    For more info, check `SUPLEMENTAL MATERIAL IV. B. <https://arxiv.org/abs/1907.04818>`_.

    Args:
        tau_exponential (float): Tau exponential factor
        amp (float): Amplitude constant
        sampling_rate (float, optional): Sampling rate. Defaults to 1.
        norm_factor (float, optional): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool, optional): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (The max height is the furthest number from 0 in the envelope, only checking the real axis/part). Defaults to True.

    Returns:
        PulseDistortion: Distortion to apply to given envelopes in PulseEvent.

    Examples:

        Imagine you want to distort a :class:`Rectangular` envelope with an `ExponentialCorrection`. You could do:

        >>> from qililab.pulse import Rectangular, BiasTeeCorrection
        >>> envelope = Rectangular().envelope(duration=50, amplitude=1.0)
        >>> distorted_envelope = ExponentialCorrection(tau_exponential=1.3, amp=2.0).apply(envelope)

        which would return a distorted envelope with the same real max height as the initial.

        >>> np.max(distorted_envelope) == np.max(envelope)
        True

        .. note::
            You can find more examples in the docstring of the :class:`PulseDistortion` base class.
    """

    name = (
        PulseDistortionName.EXPONENTIAL_CORRECTION
    )  #: Type of the correction. Enum type of PulseDistortionName class.
    tau_exponential: float  #: Tau exponential factor.
    amp: float  #: Amplitude constant. Value between 0 and 1.
    sampling_rate: float = 1.0  #: Sampling rate. Defaults to 1.

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (originally created to distort square envelopes).

        Corrects an exponential decay using a linear IIR filter.

        Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

        If `self.auto_norm` is True (default) normalizes the resulting envelope to have the same real max height than the starting one.
        (the max height is the furthest number from 0, only checking the real axis/part)
        If the corrected envelope is zero everywhere or doesn't have a real part this process is skipped.

        Finally it applies the manual `self.norm_factor` to the result, reducing the full envelope by its magnitude.

        For further details on the normalization implementation see the docstring on :class:`PulseDistortion` base class.

        Args:
            envelope (numpy.ndarray): Array representing the envelope of a pulse for each time step.

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
        """Loads ExponentialCorrection object from dictionary.

        Args:
            dictionary (dict): Dictionary object of the ExponentialCorrection object. It must include the name of the
            correction, the tau exponential factor, the amplitude, the sampling rate, the normalization factor and
            the auto normalization flag value.

        Returns:
            ExponentialCorrection: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the distortion.

        Returns:
            dict: Dictionary representation including the name of the correction, the tau exponential factor, the
            amplitude, the sampling rate, the normalization factor and the auto normalization flag value.
        """
        return {
            "name": self.name.value,
            "tau_exponential": self.tau_exponential,
            "amp": self.amp,
            "sampling_rate": self.sampling_rate,
            "norm_factor": self.norm_factor,
            "auto_norm": self.auto_norm,
        }
