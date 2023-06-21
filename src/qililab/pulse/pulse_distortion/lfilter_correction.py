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
        norm_factor (float): A coefficient to multiply the final result with, to scale it.

    Returns:
        PulseDistortion: Distortion to apply to given envelopes in PulseEvent.
    """

    name = PulseDistortionName.LFILTER
    a: list[float]
    b: list[float]
    norm_factor: float = 1.0

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (which normally get calibrated with square envelopes).

        Corrects an envelope applying the scipy.signal.lfilter.
        And then normalizes the pulse to the same real amplitude as the initial one.

        Filtered signal gets normalized with envelopes max/min heights (of the real parts)
        depending if the envelope ends more positive/negative, respectively.

        Args:
            envelope (numpy.ndarray): array representing the envelope of a pulse for each time step.

        Returns:
            numpy.ndarray: Amplitude of the envelope for each time step.
        """
        # Compute the norms before and after the filter, for both cases of the if statement
        norm = (np.max(np.real(envelope)), np.min(np.real(envelope)))
        corr_envelope = signal.lfilter(b=self.b, a=self.a, x=envelope)
        corr_norm = (np.max(np.real(corr_envelope)), np.min(np.real(corr_envelope)))

        if corr_norm[0] >= -corr_norm[1]:  # should this be with "if norm[0] >= -norm[1]:" instead?
            corr_envelope = corr_envelope * norm[0] / corr_norm[0]
        else:
            corr_envelope = corr_envelope * norm[1] / corr_norm[1]

        return corr_envelope * self.norm_factor

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
            PulseDistortionSettingsName.NORM_FACTOR.value: self.norm_factor,
            PulseDistortionSettingsName.A.value: self.a,
            PulseDistortionSettingsName.B.value: self.b,
        }
