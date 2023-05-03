"""Bias tee correction."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.typings import PulseDistortionName
from qililab.typings.enums import PulseDistortionSettingsName

from .pulse_distortion import PulseDistortion


@dataclass(unsafe_hash=True, frozen=True, eq=True)
class BiasTeeCorrection(PulseDistortion):
    """Bias tee distortion."""

    name = PulseDistortionName.BIAS_TEE_CORRECTION
    tau_bias_tee: float
    sampling_rate: float = 1.0

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Mainly to distort square envelopes.

        Corrects an exponential decay using a linear IIR filter.
        Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

        Args:
            envelope (ndarray): Square envelopes.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        # Parameters
        k = 2 * self.tau_bias_tee * self.sampling_rate

        a = [1, -1]
        b = [(k + 1) / k, -(k - 1) / k]

        # Filtered signal
        corr_envelope = signal.lfilter(b, a, envelope)
        norm = np.amax(np.abs(corr_envelope))
        corr_envelope = corr_envelope / norm

        return corr_envelope

    @classmethod
    def from_dict(cls, dictionary: dict) -> PulseDistortion:
        """Load PulseDistortion object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseDistortion object.

        Returns:
            PulseDistortion: Loaded class.
        """
        tau_bias_tee = dictionary[PulseDistortionSettingsName.TAU_BIAS_TEE.value]

        if dictionary[PulseDistortionSettingsName.SAMPLING_RATE.value]:
            sampling_rate = dictionary[PulseDistortionSettingsName.SAMPLING_RATE.value]
        else:
            sampling_rate = 1.0

        return cls(tau_bias_tee=tau_bias_tee, sampling_rate=sampling_rate)

    def to_dict(self) -> dict:
        """Return dictionary representation of the distortion.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseDistortionSettingsName.TAU_BIAS_TEE.value: self.tau_bias_tee,
            PulseDistortionSettingsName.SAMPLING_RATE.value: self.sampling_rate,
        }
