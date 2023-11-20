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
    """Bias tee distortion. Corrects for a bias tee using a linear IIR filter with time constant tau.

    For more info, check `SUPLEMENTAL MATERIAL <https://arxiv.org/abs/1907.04818>`_.

    Args:
        tau_bias_tee (float): Time constant.
        sampling_rate (float, optional): Sampling rate. Defaults to 1.
        norm_factor (float, optional): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool, optional): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (The max height is the furthest number from 0 in the envelope, only checking the real axis/part). Defaults to True.

    Returns:
        PulseDistortion: Distortion to apply to given envelopes in :class:`PulseEvent`.

    Examples:

        Imagine you want to distort a :class:`Rectangular` envelope with a BiasTeeCorrection. You could do:

        >>> from qililab.pulse import Rectangular, BiasTeeCorrection
        >>> envelope = Rectangular().envelope(duration=50, amplitude=1.0)
        >>> distorted_envelope = BiasTeeCorrection(tau_bias_tee=1.3).apply(envelope)

        which would return a distorted envelope with the same real max height as the initial.

        >>> np.max(distorted_envelope) == np.max(envelope)
        True

        .. note::
            You can find more examples in the docstring of the :class:`PulseDistortion` base class.
    """

    name = PulseDistortionName.BIAS_TEE_CORRECTION  #: Type of the correction. Enum type of PulseDistortionName class.
    tau_bias_tee: float  #: Time constant.
    sampling_rate: float = 1.0  #: Sampling rate. Defaults to 1.

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (originally created to distort square envelopes).

        Corrects for a bias tee using a linear IIR filter with time constant tau.

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
            dictionary (dict): Dictionary representation of the BiasTeeCorrection object. It must include the name of the
            correction, the tau bias tee factor, the sampling rate, the normalization factor and the
            auto normalization flag value.

        Returns:
            BiasTeeCorrection: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Return dictionary representation of the distortion.

        Returns:
            dict: Dictionary representation including the name of the correction, the tau bias tee factor,
            the sampling rate, the normalization factor and the auto normalization flag value.
        """
        return {
            "name": self.name.value,
            "tau_bias_tee": self.tau_bias_tee,
            "sampling_rate": self.sampling_rate,
            "norm_factor": self.norm_factor,
            "auto_norm": self.auto_norm,
        }
