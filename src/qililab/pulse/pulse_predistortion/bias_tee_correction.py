"""Bias tee correction."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.typings import PulsePredistortionName
from qililab.typings.enums import PulseShapeSettingsName

from .predistorted_pulse import PredistortedPulse


@dataclass(unsafe_hash=True, frozen=True, eq=True)
class BiasTeeCorrection(PredistortedPulse):
    """Bias tee correction."""

    name = PulsePredistortionName.BIAS_TEE_CORRECTION
    tau_bias_tee: float
    sampling_rate: float = 1.0

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """Distorted square envelope.

        Corrects for a bias tee using a linear IIR filter with time constant tau.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        ysig = self.pulse.envelope(amplitude, resolution)

        # Parameters
        k = 2 * self.tau_bias_tee * self.sampling_rate

        a = [1, -1]
        b = [(k + 1) / k, -(k - 1) / k]

        # Filtered signal
        ycorr = signal.lfilter(b, a, ysig)
        norm = np.amax(np.abs(ycorr))
        ycorr = ycorr / norm

        return ycorr

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.TAU_BIAS_TEE.value: self.tau_bias_tee,
        }
