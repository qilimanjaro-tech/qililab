"""Exponential decay correction."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.typings import PulseDistortionName
from qililab.typings.enums import PulseDistortionSettingsName
from qililab.utils import Factory

from .pulse_distortion import PulseDistortion


@Factory.register
@dataclass(frozen=True, eq=True)
class ExponentialCorrection(PulseDistortion):
    """Exponential decay distortion."""

    name = PulseDistortionName.EXPONENTIAL_CORRECTION
    tau_exponential: float
    amp: float
    sampling_rate: float = 1.0

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (originally created to distort square envelopes).

        Corrects an exponential decay using a linear IIR filter.
        Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

        Args:
            envelope (numpy.ndarray): array representing the envelope of a pulse for each time step.

        Returns:
            numpy.ndarray: Amplitude of the envelope for each time step.
        """
        # We normalize distorted_pulses envelopes with max heights of the real parts
        norm = np.amax(np.real(envelope))

        if self.amp >= 0.0:
            # Parameters
            alpha = 1 - np.exp(-1 / (self.sampling_rate * self.tau_exponential * (1 + self.amp)))
            k = self.amp / (1 + self.amp - alpha)

            a_1 = -(1 - alpha)
            b_0 = 1 - k + k * alpha
            b_1 = -(1 - k) * (1 - alpha)

        else:
            # Parameters
            a_1 = (self.tau_exponential * (1 + 2 * self.amp) - 1) / (2 * self.tau_exponential * (1 + self.amp) + 1)
            b_0 = (2 * self.tau_exponential + 1) / (2 * self.tau_exponential + (1 + self.amp) + 1)
            b_1 = (-2 * self.tau_exponential + 1) / (2 * self.tau_exponential * (1 + self.amp + 1))

        # Filtered signal
        corr_envelope = signal.lfilter(b=[b_0, b_1], a=[1, a_1], x=envelope)
        corr_norm = np.max(np.real(corr_envelope))
        corr_envelope = corr_envelope * norm / corr_norm

        return corr_envelope

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
        }
