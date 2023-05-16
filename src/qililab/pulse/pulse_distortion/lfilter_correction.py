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
class LFilter(PulseDistortion):
    """Bias tee distortion."""

    name = PulseDistortionName.LFILTER
    a: list[float]
    b: list[float]
    norm_factor: float = 1.0

    def apply(self, envelope: np.ndarray) -> np.ndarray:
        """Distorts envelopes (originally created to distort square envelopes).

        Corrects for a bias tee using a linear IIR filter with time constant tau.

        Args:
            envelope (numpy.ndarray): array representing the envelope of a pulse for each time step.

        Returns:
            numpy.ndarray: Amplitude of the envelope for each time step.
        """
        # Filtered signal, normalized with envelopes max heights (of the real parts)
        norm = np.amax(np.real(envelope))
        corr_envelope = signal.lfilter(b=self.b, a=self.a, x=envelope)
        corr_norm = np.max(np.real(corr_envelope))
        corr_envelope = corr_envelope * norm / corr_norm * self.norm_factor

        return corr_envelope

    @classmethod
    def from_dict(cls, dictionary: dict) -> "LFilter":
        """Load BiasTeeCorrection object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the BiasTeeCorrection object.

        Returns:
            BiasTeeCorrection: Loaded class.
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
