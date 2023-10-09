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

"""LFilter correction."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.typings import PulseDistortionName
from qililab.utils import Factory

from .pulse_distortion import PulseDistortion


@Factory.register
@dataclass(frozen=True, eq=True)
class LFilterCorrection(PulseDistortion):
    """LFilter from `scipy.signal.lfilter
    <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html>`_.

    Filters data along one-dimension with an IIR or FIR filter.

    Filters a data sequence, `x`, using a digital filter.  This works for many
    fundamental data types (including Object type).  The filter is a direct
    form II transposed implementation of the standard difference equation
    (see Notes).

    The filter function is implemented as a direct II transposed structure.
    This means that the filter implements::

        a[0]*y[n] = b[0]*x[n] + b[1]*x[n-1] + ... + b[M]*x[n-M]
                             - a[1]*y[n-1] - ... - a[N]*y[n-N]

    The rational transfer function describing this filter in the
    z-transform domain is::

                             -1              -M
                 b[0] + b[1]z  + ... + b[M] z
         Y(z) = -------------------------------- X(z)
                             -1              -N
                 a[0] + a[1]z  + ... + a[N] z

    Args:
        a (list[float]): The denominator coefficient vector in a 1-D sequence.
        b (list[float]): The numerator coefficient vector in a 1-D sequence.
        norm_factor (float, optional): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool, optional): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (The max height is the furthest number from 0 in the envelope, only checking the real axis/part). Defaults to True.

    Returns:
        PulseDistortion: Distortion to apply to given envelopes in PulseEvent.

    Examples:

        Imagine you want to distort a `Rectangular` envelope with an `LFilterCorrection`. You could do:

        >>> from qililab.pulse import Rectangular, BiasTeeCorrection
        >>> envelope = Rectangular().envelope(duration=50, amplitude=1.0)
        >>> distorted_envelope = LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6]).apply(envelope)

        which would return a distorted envelope with the same real max height as the initial.

        >>> np.max(distorted_envelope) == np.max(envelope)
        True

        .. note::
            You can find more examples in the docstring of the :class:`PulseDistortion` base class.
    """

    name = PulseDistortionName.LFILTER  #: Type of the correction.
    a: list[float]  #: The denominator coefficient vector in a 1-D sequence.
    b: list[float]  #: The numerator coefficient vector in a 1-D sequence.

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (which normally get calibrated with square envelopes).

        Corrects an envelope applying the scipy.signal.lfilter.

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
        # Filtered signal
        corr_envelope = signal.lfilter(b=self.b, a=self.a, x=envelope)
        return self.normalize_envelope(envelope=envelope, corr_envelope=corr_envelope)

    @classmethod
    def from_dict(cls, dictionary: dict) -> "LFilterCorrection":
        """Loads LFilterCorrection object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the LFilterCorrection object. It must include the name of the
            correction, the a and b parameters, the normalization factor and the auto normalization flag value.

        Returns:
            LFilterCorrection: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the distortion.

        Returns:
            dict: Dictionary representation includes the name of the correction, the a and b parameters, the normalization
            factor and the auto normalization flag value..
        """
        return {
            "name": self.name.value,
            "a": self.a,
            "b": self.b,
            "norm_factor": self.norm_factor,
            "auto_norm": self.auto_norm,
        }
