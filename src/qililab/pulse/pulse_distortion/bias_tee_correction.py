"""Bias tee correction."""
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
class BiasTeeCorrection(PulseDistortion):
    """Bias tee distortion."""

    name = PulseDistortionName.BIAS_TEE_CORRECTION
    tau_bias_tee: float
    sampling_rate: float = 1.0

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (originally created to distort square envelopes).

        Corrects for a bias tee using a linear IIR filter with time constant tau.

        Args:
            envelope (ndarray): array representing the envelope of a pulse for each time step.

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
    def from_dict(cls, dictionary: dict) -> "BiasTeeCorrection":
        """Load BiasTeeCorrection object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the BiasTeeCorrection object.

        Returns:
            BiasTeeCorrection: Loaded class.
        """
        local_dictionary = dictionary.copy()
        local_dictionary.pop(RUNCARD.NAME)
        return cls(**local_dictionary)

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
