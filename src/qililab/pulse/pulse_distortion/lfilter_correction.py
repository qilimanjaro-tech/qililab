"""LFilter correction."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.typings import PulseDistortionName, PulseDistortionSettingsName
from qililab.utils import Factory

from .pulse_distortion import PulseDistortion


@Factory.register
@dataclass(frozen=True, eq=True)
class LFilterCorrection(PulseDistortion):
    """LFilter correction from scipy.signal.lfilter
    [https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html]

    Filter data along one-dimension with an IIR or FIR filter.

    Filter a data sequence, `x`, using a digital filter.  This works for many
    fundamental data types (including Object type).  The filter is a direct
    form II transposed implementation of the standard difference equation
    (see Notes).

    The function `sosfilt` (and filter design using ``output='sos'``) should be
    preferred over `lfilter` for most filtering tasks, as second-order sections
    have fewer numerical problems.

    Notes
    -----
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
        norm_factor (float): The manual normalization factor that multiplies the envelope in the apply() method. Defaults to 1 (no effect).
        auto_norm (bool): Whether to automatically normalize the corrected envelope with the original max height in the apply() method.
            (the max height is the furthest number from 0 in the envelope, only checking the real axis/part). Defaults to True.

    Returns:
        PulseDistortion: Distortion to apply to given envelopes in PulseEvent.
    """

    name = PulseDistortionName.LFILTER
    a: list[float]
    b: list[float]

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (which normally get calibrated with square envelopes).

        Corrects an envelope applying the scipy.signal.lfilter.

        If self.auto_norm is True (default) normalizes the resulting envelope to have the same max height than the starting one.
        (the max height is the furthest number from 0 in the envelope, only checking the real axis/part)

        Finally it applies the manual self.norm_factor to the result, reducing the full envelope by its magnitude.

        Args:
            envelope (numpy.ndarray): array representing the envelope of a pulse for each time step.

        Returns:
            numpy.ndarray: Amplitude of the envelope for each time step.
        """
        # Filtered signal
        corr_envelope = signal.lfilter(b=self.b, a=self.a, x=envelope)
        return self.normalize_envelope(envelope=envelope, corr_envelope=corr_envelope)

    @classmethod
    def from_dict(cls, dictionary: dict) -> "LFilterCorrection":
        """Load LFilterCorrection object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the LFilterCorrection object.

        Returns:
            LFilterCorrection: Loaded class.
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
            PulseDistortionSettingsName.A.value: self.a,
            PulseDistortionSettingsName.B.value: self.b,
            PulseDistortionSettingsName.NORM_FACTOR.value: self.norm_factor,
            PulseDistortionSettingsName.AUTO_NORM.value: self.auto_norm,
        }
